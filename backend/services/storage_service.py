"""
Digital Ocean Spaces Storage Service
Handles all file operations with DO Spaces for centralized file management
"""

import boto3
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from botocore.exceptions import ClientError
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

class DigitalOceanStorage:
    """Handle all file operations with Digital Ocean Spaces"""
    
    def __init__(self):
        self.bucket_name = os.getenv('DO_SPACES_BUCKET', '')
        self.region = os.getenv('DO_SPACES_REGION', 'nyc3')
        self.endpoint_url = f'https://{self.region}.digitaloceanspaces.com'
        self.cdn_endpoint = f'https://{self.bucket_name}.{self.region}.cdn.digitaloceanspaces.com'
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=os.getenv('DO_SPACES_KEY'),
            aws_secret_access_key=os.getenv('DO_SPACES_SECRET'),
            region_name=self.region
        )
        
        # Ensure bucket exists and is configured
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists and has proper configuration"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Connected to DO Spaces bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket {self.bucket_name} does not exist")
            else:
                logger.error(f"Error checking bucket: {e}")
    
    def upload_file(self, file_path: str, object_key: str, 
                   content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload file to DO Spaces
        
        Args:
            file_path: Local file path to upload
            object_key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Additional metadata to store with file
        
        Returns:
            Dict with upload results
        """
        try:
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read'  # Make publicly accessible via CDN
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                object_key,
                ExtraArgs=extra_args
            )
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Return both direct and CDN URLs
            return {
                'success': True,
                'direct_url': f"{self.endpoint_url}/{self.bucket_name}/{object_key}",
                'cdn_url': f"{self.cdn_endpoint}/{object_key}",
                'object_key': object_key,
                'size': file_size,
                'content_type': content_type
            }
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_from_memory(self, file_data: bytes, object_key: str,
                          content_type: str = 'application/octet-stream',
                          metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload file from memory/bytes"""
        try:
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                **extra_args
            )
            
            return {
                'success': True,
                'cdn_url': f"{self.cdn_endpoint}/{object_key}",
                'object_key': object_key,
                'size': len(file_data)
            }
        except ClientError as e:
            logger.error(f"Failed to upload from memory: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_presigned_upload(self, object_key: str, 
                                 content_type: str = 'application/octet-stream',
                                 max_size: int = 524288000,  # 500MB default
                                 expiration: int = 3600) -> Dict[str, Any]:
        """
        Generate presigned URL for direct browser upload
        
        Args:
            object_key: S3 object key
            content_type: Expected content type
            max_size: Maximum file size in bytes
            expiration: URL expiration in seconds
        """
        try:
            # Set conditions for upload
            conditions = [
                ['content-length-range', 0, max_size],
                {'acl': 'public-read'},
                ['starts-with', '$Content-Type', content_type.split('/')[0]]
            ]
            
            # Set fields
            fields = {
                'acl': 'public-read',
                'Content-Type': content_type
            }
            
            # Generate presigned POST URL
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration
            )
            
            return {
                'success': True,
                'upload_url': response['url'],
                'fields': response['fields'],
                'object_key': object_key,
                'cdn_url': f"{self.cdn_endpoint}/{object_key}",
                'expires_in': expiration,
                'max_size': max_size
            }
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_presigned_download(self, object_key: str, 
                                   expiration: int = 3600,
                                   filename: Optional[str] = None) -> str:
        """Generate presigned URL for private download"""
        try:
            params = {'Bucket': self.bucket_name, 'Key': object_key}
            
            # Add content disposition for custom filename
            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate download URL: {e}")
            return None
    
    def download_file(self, object_key: str, local_path: str) -> bool:
        """Download file from DO Spaces to local path"""
        try:
            self.s3_client.download_file(
                self.bucket_name,
                object_key,
                local_path
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to download file {object_key}: {e}")
            return False
    
    def file_exists(self, object_key: str) -> bool:
        """Check if file exists in DO Spaces"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False
    
    def get_file_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """Get file metadata"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {}),
                'cdn_url': f"{self.cdn_endpoint}/{object_key}"
            }
        except ClientError as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    def delete_file(self, object_key: str) -> bool:
        """Delete file from DO Spaces"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted file: {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def delete_files(self, object_keys: List[str]) -> int:
        """Delete multiple files"""
        deleted_count = 0
        for key in object_keys:
            if self.delete_file(key):
                deleted_count += 1
        return deleted_count
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List files in DO Spaces with given prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"'),
                        'cdn_url': f"{self.cdn_endpoint}/{obj['Key']}"
                    })
            return files
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy file within DO Spaces"""
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key,
                ACL='public-read'
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to copy file: {e}")
            return False
    
    def move_file(self, source_key: str, dest_key: str) -> bool:
        """Move file within DO Spaces"""
        if self.copy_file(source_key, dest_key):
            return self.delete_file(source_key)
        return False
    
    def cleanup_old_files(self, prefix: str = 'temp/', days_old: int = 7) -> int:
        """
        Delete files older than specified days
        
        Args:
            prefix: Only cleanup files with this prefix
            days_old: Delete files older than this many days
        
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            files = self.list_files(prefix=prefix)
            deleted_count = 0
            
            for file in files:
                last_modified = datetime.fromisoformat(file['last_modified'].replace('+00:00', ''))
                if last_modified.replace(tzinfo=None) < cutoff_date:
                    if self.delete_file(file['key']):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files from {prefix}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0
    
    def get_bucket_usage(self) -> Dict[str, Any]:
        """Get bucket usage statistics"""
        try:
            total_size = 0
            total_count = 0
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
                        total_count += 1
            
            return {
                'total_files': total_count,
                'total_size_bytes': total_size,
                'total_size_gb': round(total_size / (1024**3), 2),
                'bucket_name': self.bucket_name,
                'region': self.region
            }
        except ClientError as e:
            logger.error(f"Failed to get bucket usage: {e}")
            return {}

# Singleton instance
storage = DigitalOceanStorage()

# Convenience functions
def upload_video(file_path: str, request_id: str, video_type: str = 'input') -> Dict[str, Any]:
    """Helper to upload video with standard naming"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = Path(file_path).name
    object_key = f"{video_type}s/{request_id}/{timestamp}_{filename}"
    return storage.upload_file(file_path, object_key, content_type='video/mp4')

def get_video_url(request_id: str, video_type: str = 'output') -> Optional[str]:
    """Get CDN URL for a video"""
    files = storage.list_files(prefix=f"{video_type}s/{request_id}/")
    if files:
        return files[0]['cdn_url']
    return None