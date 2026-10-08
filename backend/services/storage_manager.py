"""
Storage Manager
Manages project storage and implements cleanup policies to maintain disk space.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages storage for video projects with automatic cleanup.
    Maintains only the most recent projects to conserve disk space.
    """
    
    # Default configuration
    MAX_PROJECTS_PER_USER = 5  # Keep only 5 most recent projects
    MAX_PROJECT_AGE_DAYS = 7    # Delete projects older than 7 days
    MAX_STORAGE_GB = 10         # Maximum storage allocation in GB
    
    def __init__(self, base_dir: str = 'output', user_id: Optional[str] = None):
        """
        Initialize storage manager.
        
        Args:
            base_dir: Base directory for project storage
            user_id: Optional user identifier for user-specific management
        """
        self.base_dir = Path(base_dir)
        self.user_id = user_id or 'default'
        self.user_dir = self.base_dir / self.user_id
        
        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration from environment or use defaults
        self.max_projects = int(os.getenv('MAX_PROJECTS_PER_USER', self.MAX_PROJECTS_PER_USER))
        self.max_age_days = int(os.getenv('MAX_PROJECT_AGE_DAYS', self.MAX_PROJECT_AGE_DAYS))
        self.max_storage_gb = float(os.getenv('MAX_STORAGE_GB', self.MAX_STORAGE_GB))
        
        # Cache for project metadata
        self.projects_cache: Dict[str, Dict] = {}
        
        logger.info(f"Storage Manager initialized for user {self.user_id}")
        logger.info(f"Config: max_projects={self.max_projects}, max_age={self.max_age_days} days, max_storage={self.max_storage_gb} GB")
    
    def cleanup_old_projects(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Maintain only the most recent projects and remove old ones.
        
        Args:
            user_id: Optional specific user ID to clean up
            
        Returns:
            Cleanup statistics
        """
        target_user = user_id or self.user_id
        projects_dir = self.base_dir / target_user
        
        if not projects_dir.exists():
            logger.info(f"No projects directory for user {target_user}")
            return {'deleted_count': 0, 'freed_space_mb': 0}
        
        # Get all project directories
        projects = self._get_project_list(projects_dir)
        
        # Sort by creation time (newest first)
        projects.sort(key=lambda p: p['created_at'], reverse=True)
        
        deleted_count = 0
        freed_space = 0
        
        # Apply cleanup policies
        for i, project in enumerate(projects):
            should_delete = False
            reason = ""
            
            # Policy 1: Keep only N most recent projects
            if i >= self.max_projects:
                should_delete = True
                reason = f"Exceeds max projects limit ({self.max_projects})"
            
            # Policy 2: Delete projects older than max age
            project_age = datetime.now() - project['created_at']
            if project_age.days > self.max_age_days:
                should_delete = True
                reason = f"Older than {self.max_age_days} days"
            
            if should_delete:
                space_freed = self._delete_project(project['path'])
                if space_freed > 0:
                    deleted_count += 1
                    freed_space += space_freed
                    logger.info(f"Deleted project {project['name']}: {reason}")
        
        # Check total storage usage
        total_usage_gb = self.get_total_storage_usage() / (1024 ** 3)
        if total_usage_gb > self.max_storage_gb:
            logger.warning(f"Storage usage ({total_usage_gb:.2f} GB) exceeds limit ({self.max_storage_gb} GB)")
            # Delete more projects if needed
            additional_freed = self._enforce_storage_limit()
            freed_space += additional_freed
        
        cleanup_stats = {
            'deleted_count': deleted_count,
            'freed_space_mb': round(freed_space / (1024 * 1024), 2),
            'remaining_projects': len(projects) - deleted_count,
            'total_usage_gb': round(total_usage_gb, 2)
        }
        
        logger.info(f"Cleanup complete: {cleanup_stats}")
        return cleanup_stats
    
    def after_project_creation(self, project_id: str):
        """
        Called after each new project to trigger cleanup.
        
        Args:
            project_id: ID of the newly created project
        """
        logger.info(f"Post-creation cleanup for project {project_id}")
        
        # Register the new project
        self._register_project(project_id)
        
        # Trigger cleanup
        stats = self.cleanup_old_projects()
        
        logger.info(f"Storage cleanup complete. Kept {self.max_projects} most recent projects")
        
        # Send notification if storage is getting full
        usage_percent = (self.get_total_storage_usage() / (1024 ** 3)) / self.max_storage_gb * 100
        if usage_percent > 80:
            logger.warning(f"Storage usage at {usage_percent:.1f}% of limit")
    
    def _get_project_list(self, projects_dir: Path) -> List[Dict]:
        """
        Get list of all projects with metadata.
        
        Args:
            projects_dir: Directory containing projects
            
        Returns:
            List of project dictionaries
        """
        projects = []
        
        for project_path in projects_dir.iterdir():
            if project_path.is_dir():
                try:
                    # Get project metadata
                    metadata = self._get_project_metadata(project_path)
                    projects.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {project_path}: {e}")
        
        return projects
    
    def _get_project_metadata(self, project_path: Path) -> Dict:
        """
        Get metadata for a project directory.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Project metadata dictionary
        """
        # Check cache first
        cache_key = str(project_path)
        if cache_key in self.projects_cache:
            return self.projects_cache[cache_key]
        
        # Calculate project size
        total_size = 0
        file_count = 0
        for item in project_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
        
        # Get creation time
        stat = project_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        
        # Check for metadata file
        metadata_file = project_path / 'metadata.json'
        extra_metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    extra_metadata = json.load(f)
            except Exception as e:
                logger.debug(f"Failed to load metadata file: {e}")
        
        metadata = {
            'name': project_path.name,
            'path': project_path,
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'created_at': created_at,
            'modified_at': modified_at,
            'age_days': (datetime.now() - created_at).days,
            **extra_metadata
        }
        
        # Cache the metadata
        self.projects_cache[cache_key] = metadata
        
        return metadata
    
    def _delete_project(self, project_path: Path) -> int:
        """
        Delete a project directory and all its contents.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Bytes of space freed
        """
        try:
            # Get size before deletion
            metadata = self._get_project_metadata(project_path)
            size_bytes = metadata['size_bytes']
            
            # Remove from cache
            cache_key = str(project_path)
            if cache_key in self.projects_cache:
                del self.projects_cache[cache_key]
            
            # Delete the directory
            shutil.rmtree(project_path)
            
            logger.info(f"Deleted project: {project_path.name} ({metadata['size_mb']} MB)")
            return size_bytes
            
        except Exception as e:
            logger.error(f"Failed to delete project {project_path}: {e}")
            return 0
    
    def _enforce_storage_limit(self) -> int:
        """
        Enforce storage limit by deleting oldest projects.
        
        Returns:
            Bytes of space freed
        """
        total_freed = 0
        current_usage_gb = self.get_total_storage_usage() / (1024 ** 3)
        
        if current_usage_gb <= self.max_storage_gb:
            return 0
        
        logger.info(f"Enforcing storage limit: {current_usage_gb:.2f} GB > {self.max_storage_gb} GB")
        
        # Get all projects across all users
        all_projects = []
        for user_dir in self.base_dir.iterdir():
            if user_dir.is_dir():
                projects = self._get_project_list(user_dir)
                all_projects.extend(projects)
        
        # Sort by age (oldest first)
        all_projects.sort(key=lambda p: p['created_at'])
        
        # Delete oldest projects until under limit
        for project in all_projects:
            if current_usage_gb <= self.max_storage_gb:
                break
            
            space_freed = self._delete_project(project['path'])
            total_freed += space_freed
            current_usage_gb -= space_freed / (1024 ** 3)
            
            logger.info(f"Deleted {project['name']} to enforce storage limit")
        
        return total_freed
    
    def _register_project(self, project_id: str):
        """
        Register a new project in the system.
        
        Args:
            project_id: Project identifier
        """
        project_dir = self.user_dir / f'capcut_{project_id}'
        
        if project_dir.exists():
            # Create metadata file if it doesn't exist
            metadata_file = project_dir / 'metadata.json'
            if not metadata_file.exists():
                metadata = {
                    'project_id': project_id,
                    'user_id': self.user_id,
                    'created_at': datetime.now().isoformat(),
                    'type': 'capcut_project'
                }
                
                try:
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to create metadata file: {e}")
    
    def get_total_storage_usage(self) -> int:
        """
        Get total storage usage across all users.
        
        Returns:
            Total usage in bytes
        """
        total_size = 0
        
        for item in self.base_dir.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except Exception as e:
                    logger.debug(f"Failed to get size of {item}: {e}")
        
        return total_size
    
    def get_user_storage_usage(self, user_id: Optional[str] = None) -> int:
        """
        Get storage usage for a specific user.
        
        Args:
            user_id: User identifier (default: current user)
            
        Returns:
            Usage in bytes
        """
        target_user = user_id or self.user_id
        user_dir = self.base_dir / target_user
        
        if not user_dir.exists():
            return 0
        
        total_size = 0
        for item in user_dir.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except Exception as e:
                    logger.debug(f"Failed to get size of {item}: {e}")
        
        return total_size
    
    def get_storage_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive storage report.
        
        Returns:
            Storage report dictionary
        """
        total_usage = self.get_total_storage_usage()
        user_usage = self.get_user_storage_usage()
        
        # Get project counts
        all_projects = []
        for user_dir in self.base_dir.iterdir():
            if user_dir.is_dir():
                projects = self._get_project_list(user_dir)
                all_projects.extend(projects)
        
        # Calculate statistics
        oldest_project = min(all_projects, key=lambda p: p['created_at']) if all_projects else None
        newest_project = max(all_projects, key=lambda p: p['created_at']) if all_projects else None
        avg_project_size = sum(p['size_bytes'] for p in all_projects) / len(all_projects) if all_projects else 0
        
        report = {
            'total_usage_gb': round(total_usage / (1024 ** 3), 2),
            'user_usage_gb': round(user_usage / (1024 ** 3), 2),
            'usage_percent': round((total_usage / (1024 ** 3)) / self.max_storage_gb * 100, 1),
            'total_projects': len(all_projects),
            'user_projects': len([p for p in all_projects if str(p['path']).startswith(str(self.user_dir))]),
            'avg_project_size_mb': round(avg_project_size / (1024 * 1024), 2),
            'oldest_project': {
                'name': oldest_project['name'],
                'age_days': oldest_project['age_days']
            } if oldest_project else None,
            'newest_project': {
                'name': newest_project['name'],
                'age_days': newest_project['age_days']
            } if newest_project else None,
            'config': {
                'max_projects_per_user': self.max_projects,
                'max_project_age_days': self.max_age_days,
                'max_storage_gb': self.max_storage_gb
            }
        }
        
        return report
    
    def find_large_files(self, min_size_mb: float = 100) -> List[Tuple[Path, float]]:
        """
        Find large files that might be candidates for cleanup.
        
        Args:
            min_size_mb: Minimum file size in MB to report
            
        Returns:
            List of (path, size_mb) tuples
        """
        large_files = []
        min_size_bytes = min_size_mb * 1024 * 1024
        
        for item in self.base_dir.rglob('*'):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    if size >= min_size_bytes:
                        size_mb = size / (1024 * 1024)
                        large_files.append((item, size_mb))
                except Exception as e:
                    logger.debug(f"Failed to check file {item}: {e}")
        
        # Sort by size (largest first)
        large_files.sort(key=lambda x: x[1], reverse=True)
        
        return large_files
    
    def archive_project(self, project_id: str, archive_dir: Optional[str] = None) -> str:
        """
        Archive a project to a compressed file.
        
        Args:
            project_id: Project identifier
            archive_dir: Directory for archives (default: output/archives)
            
        Returns:
            Path to archive file
        """
        project_dir = self.user_dir / f'capcut_{project_id}'
        
        if not project_dir.exists():
            raise FileNotFoundError(f"Project not found: {project_id}")
        
        if not archive_dir:
            archive_dir = self.base_dir / 'archives'
        
        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Create archive
        archive_file = archive_path / f'{project_id}.tar.gz'
        
        try:
            import tarfile
            with tarfile.open(archive_file, 'w:gz') as tar:
                tar.add(project_dir, arcname=project_dir.name)
            
            # Delete original after successful archive
            shutil.rmtree(project_dir)
            
            logger.info(f"Archived project {project_id} to {archive_file}")
            return str(archive_file)
            
        except Exception as e:
            logger.error(f"Failed to archive project: {e}")
            raise