"""
Cloud Storage Service - S3-compatible storage for video files
Supports AWS S3, Digital Ocean Spaces, and compatible services
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import tempfile
import mimetypes
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

from utils.logger import get_logger

logger = get_logger(__name__)


class CloudStorageService:
    """
    Service for managing cloud storage operations.
    Supports S3-compatible storage providers.
    """
    
    def __init__(self):
        """Initialize cloud storage service with environment configuration"""
        # Determine storage provider
        self.provider = os.environ.get('STORAGE_PROVIDER', 'digitalocean').lower()
        
        if self.provider == 'digitalocean':
            self._init_digitalocean()
        elif self.provider == 's3' or self.provider == 'aws':
            self._init_aws_s3()
        elif self.provider == 'local':
            self._init_local_storage()
        else:
            logger.warning(f"Unknown storage provider: {self.provider}, falling back to local")
            self._init_local_storage()
            
    def _init_digitalocean(self):
        """Initialize Digital Ocean Spaces configuration"""
        self.endpoint_url = os.environ.get('DO_SPACES_ENDPOINT', 'https://nyc3.digitaloceanspaces.com')
        self.bucket_name = os.environ.get('DO_SPACES_BUCKET', '')
        
        # Initialize S3 client for Digital Ocean Spaces
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=os.environ.get('DO_SPACES_KEY'),
            aws_secret_access_key=os.environ.get('DO_SPACES_SECRET'),
            region_name=os.environ.get('DO_SPACES_REGION', 'nyc3')
        )
        
        self.public_url_base = f"{self.endpoint_url}/{self.bucket_name}"
        logger.info(f"Initialized Digital Ocean Spaces storage: {self.bucket_name}")
        
    def _init_aws_s3(self):
        """Initialize AWS S3 configuration"""
        self.bucket_name = os.environ.get('S3_BUCKET', '')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )
        
        self.endpoint_url = None
        self.public_url_base = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com"
        logger.info(f"Initialized AWS S3 storage: {self.bucket_name}")
        
    def _init_local_storage(self):
        """Initialize local storage as fallback"""
        self.storage_dir = Path(os.environ.get('LOCAL_STORAGE_DIR', '/tmp/cloud_storage'))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.s3_client = None
        self.bucket_name = None
        self.public_url_base = f"file://{self.storage_dir}"
        logger.info(f"Initialized local storage: {self.storage_dir}")
        
    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        public: bool = True,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to cloud storage
        
        Args:
            file_path: Path to the file to upload
            object_name: Name for the object in storage (default: use filename)
            public: Whether to make the file publicly accessible
            metadata: Optional metadata to attach to the object
            
        Returns:
            URL of the uploaded file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Generate object name if not provided
        if not object_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"uploads/{timestamp}/{file_path.name}"
            
        # Handle local storage
        if self.s3_client is None:
            return self._upload_local(file_path, object_name)
            
        try:
            # Determine content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'
                
            # Prepare upload arguments
            extra_args = {
                'ContentType': content_type
            }
            
            if public:
                extra_args['ACL'] = 'public-read'
                
            if metadata:
                extra_args['Metadata'] = metadata
                
            # Upload file
            logger.info(f"Uploading {file_path} to {self.bucket_name}/{object_name}")
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )
            
            # Return public URL
            url = f"{self.public_url_base}/{object_name}"
            logger.info(f"File uploaded successfully: {url}")
            return url
            
        except NoCredentialsError:
            logger.error("Cloud storage credentials not found")
            raise
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise
            
    def _upload_local(self, file_path: Path, object_name: str) -> str:
        """Upload file to local storage"""
        dest_path = self.storage_dir / object_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(file_path, dest_path)
        
        url = f"file://{dest_path}"
        logger.info(f"File saved locally: {url}")
        return url
        
    def download_file(
        self,
        object_name: str,
        download_path: Optional[str] = None
    ) -> str:
        """
        Download a file from cloud storage
        
        Args:
            object_name: Name of the object in storage
            download_path: Local path to save the file (default: temp directory)
            
        Returns:
            Path to the downloaded file
        """
        # Generate download path if not provided
        if not download_path:
            temp_dir = tempfile.mkdtemp(prefix="cloud_download_")
            filename = Path(object_name).name
            download_path = os.path.join(temp_dir, filename)
            
        # Handle local storage
        if self.s3_client is None:
            return self._download_local(object_name, download_path)
            
        try:
            logger.info(f"Downloading {self.bucket_name}/{object_name} to {download_path}")
            self.s3_client.download_file(
                self.bucket_name,
                object_name,
                download_path
            )
            
            logger.info(f"File downloaded successfully: {download_path}")
            return download_path
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"Object not found: {object_name}")
            else:
                logger.error(f"Failed to download file: {e}")
                raise
                
    def _download_local(self, object_name: str, download_path: str) -> str:
        """Download file from local storage"""
        source_path = self.storage_dir / object_name
        
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")
            
        Path(download_path).parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(source_path, download_path)
        
        logger.info(f"File copied from local storage: {download_path}")
        return download_path
        
    def generate_presigned_url(
        self,
        object_name: str,
        expiration: int = 3600,
        operation: str = 'get_object'
    ) -> str:
        """
        Generate a presigned URL for temporary access
        
        Args:
            object_name: Name of the object in storage
            expiration: URL expiration time in seconds
            operation: The operation to allow (get_object or put_object)
            
        Returns:
            Presigned URL
        """
        if self.s3_client is None:
            # Local storage - return file URL
            return f"file://{self.storage_dir}/{object_name}"
            
        try:
            url = self.s3_client.generate_presigned_url(
                operation,
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {object_name} (expires in {expiration}s)")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
            
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from cloud storage
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            True if deleted successfully
        """
        if self.s3_client is None:
            # Local storage
            file_path = self.storage_dir / object_name
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted local file: {file_path}")
                return True
            return False
            
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            
            logger.info(f"Deleted object: {self.bucket_name}/{object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False
            
    def list_files(
        self,
        prefix: str = '',
        max_items: int = 1000
    ) -> list:
        """
        List files in cloud storage
        
        Args:
            prefix: Prefix to filter objects
            max_items: Maximum number of items to return
            
        Returns:
            List of object names
        """
        if self.s3_client is None:
            # Local storage
            files = []
            search_dir = self.storage_dir / prefix if prefix else self.storage_dir
            
            if search_dir.exists():
                for file_path in search_dir.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(self.storage_dir)
                        files.append(str(relative_path))
                        if len(files) >= max_items:
                            break
            return files
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_items
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append(obj['Key'])
                    
            logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
            
    def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file in storage
        
        Args:
            object_name: Name of the object
            
        Returns:
            Dictionary with file information or None if not found
        """
        if self.s3_client is None:
            # Local storage
            file_path = self.storage_dir / object_name
            if file_path.exists():
                stat = file_path.stat()
                return {
                    'size': stat.st_size,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime),
                    'content_type': mimetypes.guess_type(str(file_path))[0]
                }
            return None
            
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                logger.error(f"Failed to get file info: {e}")
                raise
                
    def cleanup_old_files(
        self,
        prefix: str = '',
        max_age_days: int = 7
    ) -> int:
        """
        Clean up old files from storage
        
        Args:
            prefix: Prefix to filter objects
            max_age_days: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        files = self.list_files(prefix=prefix)
        
        for file_name in files:
            info = self.get_file_info(file_name)
            if info and info['last_modified'] < cutoff_date:
                if self.delete_file(file_name):
                    deleted_count += 1
                    
        logger.info(f"Cleaned up {deleted_count} files older than {max_age_days} days")
        return deleted_count