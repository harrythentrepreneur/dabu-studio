/**
 * Chunked file upload handler for Digital Ocean Spaces
 * Handles direct browser-to-DO Spaces uploads with progress tracking
 */

interface UploadOptions {
  onProgress?: (progress: number) => void;
  onStatusChange?: (status: string) => void;
  chunkSize?: number; // Size in MB, default 100MB
}

interface UploadResult {
  success: boolean;
  publicUrl?: string;
  error?: string;
}

interface PresignedUrlResponse {
  uploadUrl: string;
  publicUrl: string;
  key: string;
  expiresIn: number;
  multipart?: boolean;
  uploadParts?: Array<{
    partNumber: number;
    uploadUrl: string;
    start: number;
    end: number;
  }>;
}

export class UploadHandler {
  private abortController: AbortController | null = null;

  /**
   * Upload a file to Digital Ocean Spaces
   */
  async uploadFile(
    file: File,
    options: UploadOptions = {}
  ): Promise<UploadResult> {
    const { onProgress, onStatusChange, chunkSize = 100 } = options;

    try {
      this.abortController = new AbortController();
      
      // Get presigned URL(s) from our API
      onStatusChange?.('Preparing upload...');
      const presignedData = await this.getPresignedUrl(file, chunkSize);

      if (!presignedData.multipart) {
        // Single upload for small files
        return await this.singleUpload(file, presignedData, onProgress, onStatusChange);
      } else {
        // Multipart upload for large files
        return await this.multipartUpload(file, presignedData, onProgress, onStatusChange);
      }
    } catch (error) {
      console.error('Upload error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed',
      };
    }
  }

  /**
   * Get presigned URL(s) from our API
   */
  private async getPresignedUrl(
    file: File,
    chunkSizeMB: number
  ): Promise<PresignedUrlResponse> {
    const chunkSizeBytes = chunkSizeMB * 1024 * 1024;
    const needsMultipart = file.size > chunkSizeBytes;

    const endpoint = needsMultipart ? 'PUT' : 'POST';
    const response = await fetch('/api/upload-url', {
      method: endpoint,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fileName: file.name,
        fileType: file.type || 'application/octet-stream',
        fileSize: file.size,
      }),
      signal: this.abortController?.signal,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get upload URL');
    }

    return response.json();
  }

  /**
   * Upload a single file directly to DO Spaces
   */
  private async singleUpload(
    file: File,
    presignedData: PresignedUrlResponse,
    onProgress?: (progress: number) => void,
    onStatusChange?: (status: string) => void
  ): Promise<UploadResult> {
    onStatusChange?.('Uploading file...');

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress?.(progress);
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          onStatusChange?.('Upload complete');
          resolve({
            success: true,
            publicUrl: presignedData.publicUrl,
          });
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      // Handle errors
      xhr.addEventListener('error', (event) => {
        console.error('Upload XHR error:', event);
        console.error('Upload URL:', presignedData.uploadUrl);
        console.error('File type:', file.type);
        reject(new Error('Network error during upload - Check CORS configuration'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'));
      });

      // Set up the request
      xhr.open('PUT', presignedData.uploadUrl);
      xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');

      // Abort handling
      if (this.abortController) {
        this.abortController.signal.addEventListener('abort', () => {
          xhr.abort();
        });
      }

      // Send the file
      xhr.send(file);
    });
  }

  /**
   * Upload a large file in chunks
   */
  private async multipartUpload(
    file: File,
    presignedData: PresignedUrlResponse,
    onProgress?: (progress: number) => void,
    onStatusChange?: (status: string) => void
  ): Promise<UploadResult> {
    if (!presignedData.uploadParts) {
      throw new Error('No upload parts provided for multipart upload');
    }

    const totalParts = presignedData.uploadParts.length;
    let completedParts = 0;
    let totalUploaded = 0;

    onStatusChange?.(`Uploading in ${totalParts} parts...`);

    // Upload parts in parallel (max 4 concurrent)
    const CONCURRENT_UPLOADS = 4;
    const uploadQueue = [...presignedData.uploadParts];
    const activeUploads: Promise<void>[] = [];

    const uploadPart = async (part: { partNumber: number; uploadUrl: string; start: number; end: number }) => {
      const chunk = file.slice(part.start, part.end);
      
      const xhr = new XMLHttpRequest();
      
      return new Promise<void>((resolve, reject) => {
        // Track part progress
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const overallProgress = Math.round(
              ((totalUploaded + event.loaded) / file.size) * 100
            );
            onProgress?.(overallProgress);
          }
        });

        // Handle completion
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            completedParts++;
            totalUploaded += (part.end - part.start);
            onStatusChange?.(`Uploaded part ${completedParts}/${totalParts}`);
            resolve();
          } else {
            reject(new Error(`Part ${part.partNumber} upload failed`));
          }
        });

        // Handle errors
        xhr.addEventListener('error', () => {
          reject(new Error(`Network error uploading part ${part.partNumber}`));
        });

        xhr.addEventListener('abort', () => {
          reject(new Error('Upload cancelled'));
        });

        // Set up the request
        xhr.open('PUT', part.uploadUrl);
        xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');

        // Abort handling
        if (this.abortController) {
          this.abortController.signal.addEventListener('abort', () => {
            xhr.abort();
          });
        }

        // Send the chunk
        xhr.send(chunk);
      });
    };

    // Process upload queue
    while (uploadQueue.length > 0 || activeUploads.length > 0) {
      // Start new uploads if we have capacity
      while (activeUploads.length < CONCURRENT_UPLOADS && uploadQueue.length > 0) {
        const part = uploadQueue.shift()!;
        const uploadPromise = uploadPart(part).then(() => {
          // Remove from active uploads when done
          const index = activeUploads.indexOf(uploadPromise);
          if (index > -1) {
            activeUploads.splice(index, 1);
          }
        });
        activeUploads.push(uploadPromise);
      }

      // Wait for at least one upload to complete
      if (activeUploads.length > 0) {
        await Promise.race(activeUploads);
      }
    }

    onStatusChange?.('Upload complete');
    return {
      success: true,
      publicUrl: presignedData.publicUrl,
    };
  }

  /**
   * Cancel ongoing upload
   */
  cancelUpload() {
    this.abortController?.abort();
    this.abortController = null;
  }
}

// Export singleton instance
export const uploadHandler = new UploadHandler();