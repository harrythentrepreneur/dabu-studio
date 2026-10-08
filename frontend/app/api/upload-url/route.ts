import { NextRequest, NextResponse } from 'next/server';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import crypto from 'crypto';

// Initialize S3 client for Digital Ocean Spaces
const s3Client = new S3Client({
  endpoint: process.env.DO_SPACES_ENDPOINT || 'https://sfo3.digitaloceanspaces.com',
  region: process.env.DO_SPACES_REGION || 'sfo3',
  credentials: {
    accessKeyId: process.env.DO_SPACES_KEY!,
    secretAccessKey: process.env.DO_SPACES_SECRET!,
  },
});

const BUCKET_NAME = process.env.DO_SPACES_BUCKET || '';

export async function POST(request: NextRequest) {
  try {
    const { fileName, fileType, fileSize } = await request.json();

    if (!fileName || !fileType) {
      return NextResponse.json(
        { error: 'Missing required fields: fileName, fileType' },
        { status: 400 }
      );
    }

    // Validate file size (max 2GB)
    const MAX_SIZE = 2 * 1024 * 1024 * 1024; // 2GB
    if (fileSize && fileSize > MAX_SIZE) {
      return NextResponse.json(
        { error: 'File size exceeds maximum allowed size of 2GB' },
        { status: 400 }
      );
    }

    // Generate unique key
    const timestamp = Date.now();
    const uniqueId = crypto.randomBytes(6).toString('hex');
    const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9.-]/g, '_');
    const key = `uploads/${timestamp}_${uniqueId}_${sanitizedFileName}`;

    // Create presigned URL for PUT operation
    const command = new PutObjectCommand({
      Bucket: BUCKET_NAME,
      Key: key,
      ContentType: fileType,
      // Note: ACL is removed as it may cause issues with presigned URLs
    });

    const uploadUrl = await getSignedUrl(s3Client, command, {
      expiresIn: 900, // 15 minutes
    });

    // Construct the public URL for the file
    const publicUrl = `https://${BUCKET_NAME}.${process.env.DO_SPACES_REGION}.digitaloceanspaces.com/${key}`;

    // Debug logging
    console.log('Generated presigned URL:', {
      uploadUrl: uploadUrl.substring(0, 100) + '...',
      publicUrl,
      bucket: BUCKET_NAME,
      key,
      endpoint: process.env.DO_SPACES_ENDPOINT,
    });

    return NextResponse.json({
      uploadUrl,
      publicUrl,
      key,
      expiresIn: 900,
    });
  } catch (error) {
    console.error('Error generating presigned URL:', error);
    return NextResponse.json(
      { error: 'Failed to generate upload URL' },
      { status: 500 }
    );
  }
}

// Support for multipart upload (for files > 100MB)
export async function PUT(request: NextRequest) {
  try {
    const { fileName, fileType, fileSize, parts } = await request.json();

    if (!fileName || !fileType || !fileSize) {
      return NextResponse.json(
        { error: 'Missing required fields: fileName, fileType, fileSize' },
        { status: 400 }
      );
    }

    // Calculate number of parts (100MB per part)
    const PART_SIZE = 100 * 1024 * 1024; // 100MB
    const numParts = Math.ceil(fileSize / PART_SIZE);

    if (numParts === 1) {
      // For small files, just use single upload
      return POST(request);
    }

    // Generate unique key
    const timestamp = Date.now();
    const uniqueId = crypto.randomBytes(6).toString('hex');
    const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9.-]/g, '_');
    const key = `uploads/${timestamp}_${uniqueId}_${sanitizedFileName}`;

    // Generate presigned URLs for each part
    const uploadParts = [];
    for (let i = 0; i < numParts; i++) {
      const start = i * PART_SIZE;
      const end = Math.min(start + PART_SIZE, fileSize);
      
      const command = new PutObjectCommand({
        Bucket: BUCKET_NAME,
        Key: `${key}.part${i + 1}`,
        ContentType: fileType,
        // ACL removed - bucket policy handles public access
      });

      const uploadUrl = await getSignedUrl(s3Client, command, {
        expiresIn: 1800, // 30 minutes for multipart
      });

      uploadParts.push({
        partNumber: i + 1,
        uploadUrl,
        start,
        end,
      });
    }

    const publicUrl = `${process.env.DO_SPACES_ENDPOINT}/${BUCKET_NAME}/${key}`;

    return NextResponse.json({
      multipart: true,
      uploadParts,
      publicUrl,
      key,
      expiresIn: 1800,
    });
  } catch (error) {
    console.error('Error generating multipart upload URLs:', error);
    return NextResponse.json(
      { error: 'Failed to generate multipart upload URLs' },
      { status: 500 }
    );
  }
}