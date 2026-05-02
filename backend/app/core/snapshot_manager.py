"""
Schema Snapshot Manager for saving and loading database schema snapshots
Stores snapshots as JSON files for version control and drift detection
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import logging
import uuid

from app.models.schema import DatabaseSchema, SchemaSnapshot
from app.config import settings

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Manage schema snapshots - save, load, list, and delete"""
    
    def __init__(self, snapshots_dir: Optional[str] = None):
        """
        Initialize snapshot manager.
        
        Args:
            snapshots_dir: Directory to store snapshots (uses config default if None)
        """
        self.snapshots_dir = Path(snapshots_dir or settings.snapshots_dir)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Create snapshots directory if it doesn't exist"""
        try:
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Snapshots directory ready: {self.snapshots_dir}")
        except Exception as e:
            logger.error(f"Failed to create snapshots directory: {e}")
            raise
    
    def save_snapshot(
        self,
        database_schema: DatabaseSchema,
        snapshot_type: str = "manual",
        notes: Optional[str] = None
    ) -> SchemaSnapshot:
        """
        Save a database schema snapshot to disk.
        
        Args:
            database_schema: Database schema to snapshot
            snapshot_type: Type of snapshot (manual, scheduled, pre-migration)
            notes: Optional notes about this snapshot
            
        Returns:
            SchemaSnapshot: The saved snapshot with metadata
        """
        # Generate unique snapshot ID
        snapshot_id = self._generate_snapshot_id(database_schema.database_name)
        
        # Create snapshot object
        snapshot = SchemaSnapshot(
            snapshot_id=snapshot_id,
            database_schema=database_schema,
            snapshot_timestamp=datetime.utcnow(),
            snapshot_type=snapshot_type,
            notes=notes
        )
        
        # Save to file
        file_path = self._get_snapshot_path(snapshot_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Convert to JSON using Pydantic's model_dump
                json_data = snapshot.model_dump(mode='json')
                json.dump(json_data, f, indent=2, default=str)
            
            logger.info(f"Saved snapshot: {snapshot_id} to {file_path}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to save snapshot {snapshot_id}: {e}")
            raise
    
    def load_snapshot(self, snapshot_id: str) -> SchemaSnapshot:
        """
        Load a schema snapshot from disk.
        
        Args:
            snapshot_id: Unique snapshot identifier
            
        Returns:
            SchemaSnapshot: The loaded snapshot
            
        Raises:
            FileNotFoundError: If snapshot doesn't exist
        """
        file_path = self._get_snapshot_path(snapshot_id)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Parse JSON back to Pydantic model
            snapshot = SchemaSnapshot(**json_data)
            
            logger.info(f"Loaded snapshot: {snapshot_id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            raise
    
    def list_snapshots(self) -> List[dict]:
        """
        List all available snapshots with metadata.
        
        Returns:
            List[dict]: List of snapshot metadata (id, timestamp, type, database)
        """
        snapshots = []
        
        try:
            for file_path in self.snapshots_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # Extract key metadata
                    snapshot_info = {
                        "snapshot_id": json_data.get("snapshot_id"),
                        "database_name": json_data.get("database_schema", {}).get("database_name"),
                        "snapshot_timestamp": json_data.get("snapshot_timestamp"),
                        "snapshot_type": json_data.get("snapshot_type"),
                        "notes": json_data.get("notes"),
                        "total_tables": json_data.get("database_schema", {}).get("total_tables"),
                        "file_path": str(file_path)
                    }
                    
                    snapshots.append(snapshot_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to read snapshot file {file_path}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            snapshots.sort(key=lambda x: x.get("snapshot_timestamp", ""), reverse=True)
            
            logger.info(f"Found {len(snapshots)} snapshots")
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot from disk.
        
        Args:
            snapshot_id: Unique snapshot identifier
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        file_path = self._get_snapshot_path(snapshot_id)
        
        if not file_path.exists():
            logger.warning(f"Snapshot not found for deletion: {snapshot_id}")
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            return False
    
    def get_latest_snapshot(self, database_name: Optional[str] = None) -> Optional[SchemaSnapshot]:
        """
        Get the most recent snapshot, optionally filtered by database name.
        
        Args:
            database_name: Filter by database name (None = any database)
            
        Returns:
            SchemaSnapshot: Latest snapshot or None if no snapshots exist
        """
        snapshots = self.list_snapshots()
        
        if database_name:
            snapshots = [s for s in snapshots if s.get("database_name") == database_name]
        
        if not snapshots:
            return None
        
        # Get the first one (already sorted by timestamp)
        latest = snapshots[0]
        return self.load_snapshot(latest["snapshot_id"])
    
    def export_snapshot_to_json(self, snapshot_id: str, output_path: str) -> bool:
        """
        Export a snapshot to a custom location.
        
        Args:
            snapshot_id: Snapshot to export
            output_path: Destination file path
            
        Returns:
            bool: True if exported successfully
        """
        try:
            snapshot = self.load_snapshot(snapshot_id)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = snapshot.model_dump(mode='json')
                json.dump(json_data, f, indent=2, default=str)
            
            logger.info(f"Exported snapshot {snapshot_id} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export snapshot {snapshot_id}: {e}")
            return False
    
    def import_snapshot_from_json(self, input_path: str) -> SchemaSnapshot:
        """
        Import a snapshot from a JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            SchemaSnapshot: The imported snapshot
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            snapshot = SchemaSnapshot(**json_data)
            
            # Save to snapshots directory
            file_path = self._get_snapshot_path(snapshot.snapshot_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            logger.info(f"Imported snapshot {snapshot.snapshot_id} from {input_path}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to import snapshot from {input_path}: {e}")
            raise
    
    def _generate_snapshot_id(self, database_name: str) -> str:
        """
        Generate a unique snapshot ID.
        
        Args:
            database_name: Name of the database
            
        Returns:
            str: Unique snapshot ID (format: dbname_timestamp_uuid)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        
        # Clean database name for filename
        clean_db_name = database_name.lower().replace(' ', '_').replace('-', '_')
        
        return f"{clean_db_name}_{timestamp}_{short_uuid}"
    
    def _get_snapshot_path(self, snapshot_id: str) -> Path:
        """
        Get the file path for a snapshot.
        
        Args:
            snapshot_id: Snapshot identifier
            
        Returns:
            Path: Full path to snapshot file
        """
        return self.snapshots_dir / f"{snapshot_id}.json"
    
    def cleanup_old_snapshots(self, keep_count: int = 10, database_name: Optional[str] = None) -> int:
        """
        Delete old snapshots, keeping only the most recent ones.
        
        Args:
            keep_count: Number of snapshots to keep
            database_name: Filter by database name (None = all databases)
            
        Returns:
            int: Number of snapshots deleted
        """
        snapshots = self.list_snapshots()
        
        if database_name:
            snapshots = [s for s in snapshots if s.get("database_name") == database_name]
        
        if len(snapshots) <= keep_count:
            logger.info(f"No cleanup needed: {len(snapshots)} snapshots (keeping {keep_count})")
            return 0
        
        # Delete oldest snapshots
        to_delete = snapshots[keep_count:]
        deleted_count = 0
        
        for snapshot_info in to_delete:
            snapshot_id = snapshot_info.get("snapshot_id")
            if snapshot_id and self.delete_snapshot(snapshot_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old snapshots")
        return deleted_count


# Global snapshot manager instance
snapshot_manager = SnapshotManager()


def save_snapshot(
    database_schema: DatabaseSchema,
    snapshot_type: str = "manual",
    notes: Optional[str] = None
) -> SchemaSnapshot:
    """
    Convenience function to save a snapshot using the global manager.
    
    Args:
        database_schema: Database schema to snapshot
        snapshot_type: Type of snapshot (manual, scheduled, pre-migration)
        notes: Optional notes about this snapshot
        
    Returns:
        SchemaSnapshot: The saved snapshot
    """
    return snapshot_manager.save_snapshot(database_schema, snapshot_type, notes)


def load_snapshot(snapshot_id: str) -> SchemaSnapshot:
    """
    Convenience function to load a snapshot using the global manager.
    
    Args:
        snapshot_id: Unique snapshot identifier
        
    Returns:
        SchemaSnapshot: The loaded snapshot
    """
    return snapshot_manager.load_snapshot(snapshot_id)


def list_snapshots() -> List[dict]:
    """
    Convenience function to list snapshots using the global manager.
    
    Returns:
        List[dict]: List of snapshot metadata
    """
    return snapshot_manager.list_snapshots()


# Made with Bob