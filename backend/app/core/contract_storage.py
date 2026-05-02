"""
Contract Storage Manager for DataContractIQ MCP Server
Handles saving, loading, and managing data contracts as JSON files
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import logging
import uuid

from app.models.contract import (
    DataContract,
    ContractStatus,
    ContractMetadata
)
from app.config import settings

logger = logging.getLogger(__name__)


class ContractStorage:
    """Manage data contract storage and retrieval"""
    
    def __init__(self, contracts_dir: Optional[str] = None):
        """
        Initialize contract storage manager.
        
        Args:
            contracts_dir: Directory to store contracts (uses config default if None)
        """
        self.contracts_dir = Path(contracts_dir or settings.contracts_dir)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """Create contracts directory if it doesn't exist"""
        try:
            self.contracts_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Contracts directory ready: {self.contracts_dir}")
        except Exception as e:
            logger.error(f"Failed to create contracts directory: {e}")
            raise
    
    def save_contract(
        self,
        contract: DataContract,
        approved_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DataContract:
        """
        Save a data contract to disk.
        
        Args:
            contract: Contract to save
            approved_by: User who approved (if applicable)
            notes: Approval notes (if applicable)
            
        Returns:
            DataContract: The saved contract with updated metadata
        """
        # Update metadata
        now = datetime.utcnow()
        
        if not contract.metadata.contract_id:
            contract.metadata.contract_id = self._generate_contract_id(contract.table_name)
        
        contract.metadata.updated_at = now
        
        if approved_by:
            contract.metadata.status = ContractStatus.APPROVED
            contract.metadata.approved_by = approved_by
            contract.metadata.approved_at = now
            if notes:
                contract.metadata.approval_notes = notes
        
        # Save to file
        file_path = self._get_contract_path(contract.metadata.contract_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Convert to JSON using Pydantic's model_dump
                json_data = contract.model_dump(mode='json')
                json.dump(json_data, f, indent=2, default=str)
            
            logger.info(f"Saved contract: {contract.metadata.contract_id} to {file_path}")
            return contract
            
        except Exception as e:
            logger.error(f"Failed to save contract {contract.metadata.contract_id}: {e}")
            raise
    
    def load_contract(self, contract_id: str) -> DataContract:
        """
        Load a contract from disk.
        
        Args:
            contract_id: Unique contract identifier
            
        Returns:
            DataContract: The loaded contract
            
        Raises:
            FileNotFoundError: If contract doesn't exist
        """
        file_path = self._get_contract_path(contract_id)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Contract not found: {contract_id}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Parse JSON back to Pydantic model
            contract = DataContract(**json_data)
            
            logger.info(f"Loaded contract: {contract_id}")
            return contract
            
        except Exception as e:
            logger.error(f"Failed to load contract {contract_id}: {e}")
            raise
    
    def list_contracts(
        self,
        status: Optional[ContractStatus] = None,
        table_name: Optional[str] = None
    ) -> List[Dict]:
        """
        List all contracts with optional filtering.
        
        Args:
            status: Filter by status (None = all)
            table_name: Filter by table name (None = all)
            
        Returns:
            List[Dict]: List of contract metadata
        """
        contracts = []
        
        try:
            for file_path in self.contracts_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # Extract key metadata
                    contract_info = {
                        "contract_id": json_data.get("metadata", {}).get("contract_id"),
                        "table_name": json_data.get("table_name"),
                        "schema_name": json_data.get("schema_name"),
                        "status": json_data.get("metadata", {}).get("status"),
                        "version": json_data.get("metadata", {}).get("version"),
                        "created_at": json_data.get("metadata", {}).get("created_at"),
                        "updated_at": json_data.get("metadata", {}).get("updated_at"),
                        "approved_at": json_data.get("metadata", {}).get("approved_at"),
                        "approved_by": json_data.get("metadata", {}).get("approved_by"),
                        "file_path": str(file_path)
                    }
                    
                    # Apply filters
                    if status and contract_info["status"] != status.value:
                        continue
                    
                    if table_name and contract_info["table_name"] != table_name:
                        continue
                    
                    contracts.append(contract_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to read contract file {file_path}: {e}")
                    continue
            
            # Sort by updated_at (newest first)
            contracts.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            
            logger.info(f"Found {len(contracts)} contracts")
            return contracts
            
        except Exception as e:
            logger.error(f"Failed to list contracts: {e}")
            return []
    
    def delete_contract(self, contract_id: str) -> bool:
        """
        Delete a contract from disk.
        
        Args:
            contract_id: Unique contract identifier
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        file_path = self._get_contract_path(contract_id)
        
        if not file_path.exists():
            logger.warning(f"Contract not found for deletion: {contract_id}")
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Deleted contract: {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete contract {contract_id}: {e}")
            return False
    
    def get_latest_contract(
        self,
        table_name: str,
        status: Optional[ContractStatus] = None
    ) -> Optional[DataContract]:
        """
        Get the most recent contract for a table.
        
        Args:
            table_name: Table name to find contract for
            status: Filter by status (None = any status)
            
        Returns:
            DataContract: Latest contract or None if not found
        """
        contracts = self.list_contracts(status=status, table_name=table_name)
        
        if not contracts:
            return None
        
        # Get the first one (already sorted by updated_at)
        latest = contracts[0]
        return self.load_contract(latest["contract_id"])
    
    def get_contract_by_table(
        self,
        table_name: str,
        status: Optional[ContractStatus] = ContractStatus.APPROVED
    ) -> Optional[DataContract]:
        """
        Get the approved contract for a table.
        
        Args:
            table_name: Table name
            status: Contract status to filter by (default: approved)
            
        Returns:
            DataContract: Contract or None if not found
        """
        return self.get_latest_contract(table_name, status)
    
    def update_contract_status(
        self,
        contract_id: str,
        new_status: ContractStatus,
        updated_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DataContract:
        """
        Update the status of a contract.
        
        Args:
            contract_id: Contract to update
            new_status: New status
            updated_by: User making the update
            notes: Update notes
            
        Returns:
            DataContract: Updated contract
        """
        contract = self.load_contract(contract_id)
        
        contract.metadata.status = new_status
        contract.metadata.updated_at = datetime.utcnow()
        
        if updated_by:
            contract.metadata.updated_by = updated_by
        
        if notes:
            if not contract.notes:
                contract.notes = notes
            else:
                contract.notes += f"\n\n{notes}"
        
        return self.save_contract(contract)
    
    def archive_contract(self, contract_id: str, archived_by: Optional[str] = None) -> DataContract:
        """
        Archive a contract (mark as archived, don't delete).
        
        Args:
            contract_id: Contract to archive
            archived_by: User archiving the contract
            
        Returns:
            DataContract: Archived contract
        """
        return self.update_contract_status(
            contract_id,
            ContractStatus.ARCHIVED,
            updated_by=archived_by,
            notes="Contract archived"
        )
    
    def export_contract(self, contract_id: str, output_path: str) -> bool:
        """
        Export a contract to a custom location.
        
        Args:
            contract_id: Contract to export
            output_path: Destination file path
            
        Returns:
            bool: True if exported successfully
        """
        try:
            contract = self.load_contract(contract_id)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = contract.model_dump(mode='json')
                json.dump(json_data, f, indent=2, default=str)
            
            logger.info(f"Exported contract {contract_id} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export contract {contract_id}: {e}")
            return False
    
    def import_contract(self, input_path: str) -> DataContract:
        """
        Import a contract from a JSON file.
        
        Args:
            input_path: Path to JSON file
            
        Returns:
            DataContract: The imported contract
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            contract = DataContract(**json_data)
            
            # Save to contracts directory
            saved_contract = self.save_contract(contract)
            
            logger.info(f"Imported contract {contract.metadata.contract_id} from {input_path}")
            return saved_contract
            
        except Exception as e:
            logger.error(f"Failed to import contract from {input_path}: {e}")
            raise
    
    def get_contracts_summary(self) -> Dict:
        """
        Get summary statistics about contracts.
        
        Returns:
            Dict: Summary with counts by status, tables covered, etc.
        """
        all_contracts = self.list_contracts()
        
        summary = {
            "total_contracts": len(all_contracts),
            "by_status": {
                "draft": 0,
                "approved": 0,
                "outdated": 0,
                "archived": 0
            },
            "tables_covered": set(),
            "latest_update": None
        }
        
        for contract in all_contracts:
            status = contract.get("status", "draft")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            table_name = contract.get("table_name")
            if table_name:
                summary["tables_covered"].add(table_name)
            
            updated_at = contract.get("updated_at")
            if updated_at:
                if not summary["latest_update"] or updated_at > summary["latest_update"]:
                    summary["latest_update"] = updated_at
        
        summary["tables_covered"] = list(summary["tables_covered"])
        summary["tables_count"] = len(summary["tables_covered"])
        
        return summary
    
    def _generate_contract_id(self, table_name: str) -> str:
        """
        Generate a unique contract ID.
        
        Args:
            table_name: Name of the table
            
        Returns:
            str: Unique contract ID (format: tablename_timestamp_uuid)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        
        # Clean table name for filename
        clean_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        
        return f"{clean_table_name}_{timestamp}_{short_uuid}"
    
    def _get_contract_path(self, contract_id: str) -> Path:
        """
        Get the file path for a contract.
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            Path: Full path to contract file
        """
        return self.contracts_dir / f"{contract_id}.json"


# Global contract storage instance
contract_storage = ContractStorage()


def save_contract(
    contract: DataContract,
    approved_by: Optional[str] = None,
    notes: Optional[str] = None
) -> DataContract:
    """
    Convenience function to save a contract using the global storage.
    
    Args:
        contract: Contract to save
        approved_by: User who approved (if applicable)
        notes: Approval notes (if applicable)
        
    Returns:
        DataContract: The saved contract
    """
    return contract_storage.save_contract(contract, approved_by, notes)


def load_contract(contract_id: str) -> DataContract:
    """
    Convenience function to load a contract using the global storage.
    
    Args:
        contract_id: Unique contract identifier
        
    Returns:
        DataContract: The loaded contract
    """
    return contract_storage.load_contract(contract_id)


def list_contracts(
    status: Optional[ContractStatus] = None,
    table_name: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to list contracts using the global storage.
    
    Args:
        status: Filter by status (None = all)
        table_name: Filter by table name (None = all)
        
    Returns:
        List[Dict]: List of contract metadata
    """
    return contract_storage.list_contracts(status, table_name)


def get_contract_by_table(
    table_name: str,
    status: Optional[ContractStatus] = ContractStatus.APPROVED
) -> Optional[DataContract]:
    """
    Convenience function to get contract by table name.
    
    Args:
        table_name: Table name
        status: Contract status to filter by (default: approved)
        
    Returns:
        DataContract: Contract or None if not found
    """
    return contract_storage.get_contract_by_table(table_name, status)


# Made with Bob