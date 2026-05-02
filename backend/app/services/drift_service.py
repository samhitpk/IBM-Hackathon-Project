"""
Drift Detection Service Layer for DataContractIQ
Business logic for detecting schema drift against approved contracts
"""
import logging
from typing import Optional, List, Dict
from datetime import datetime
import time

from app.models.contract import DriftReport, DriftDetectionResponse
from app.core.drift_detector import DriftDetector
from app.core.contract_storage import get_contract_by_table, list_contracts
from app.models.contract import ContractStatus

logger = logging.getLogger(__name__)


def detect_drift_for_table(
    table_name: str,
    contract_id: Optional[str] = None
) -> DriftDetectionResponse:
    """
    Detect schema drift for a specific table.
    
    Args:
        table_name: Table to check for drift
        contract_id: Specific contract to compare against (uses latest approved if None)
        
    Returns:
        DriftDetectionResponse with detailed drift report
        
    Raises:
        ValueError: If no approved contract found for table
        Exception: If drift detection fails
    """
    start_time = time.time()
    
    try:
        logger.info(f"Detecting drift for table: {table_name}")
        
        # Load contract
        if contract_id:
            from app.core.contract_storage import load_contract
            contract = load_contract(contract_id)
        else:
            contract = get_contract_by_table(table_name, status=ContractStatus.APPROVED)
            
        if contract is None:
            raise ValueError(f"No approved contract found for table: {table_name}")
        
        # Detect drift
        detector = DriftDetector()
        drift_report = detector.detect_drift(
            table_name=table_name,
            contract=contract
        )
        
        detection_time = time.time() - start_time
        
        logger.info(
            f"Drift detection complete for {table_name}: "
            f"{len(drift_report.changes)} changes found in {detection_time:.2f}s"
        )
        
        return DriftDetectionResponse(
            drift_report=drift_report,
            detection_time_seconds=detection_time,
            success=True,
            message=f"Drift detection completed for table '{table_name}'"
        )
        
    except ValueError as e:
        detection_time = time.time() - start_time
        logger.warning(f"Drift detection failed for {table_name}: {e}")
        raise
        
    except Exception as e:
        detection_time = time.time() - start_time
        logger.error(f"Error detecting drift for {table_name}: {e}", exc_info=True)
        raise


def detect_drift_for_all_approved() -> Dict[str, DriftReport]:
    """
    Detect drift for all tables with approved contracts.
    
    Returns:
        Dict mapping table names to drift reports
    """
    logger.info("Detecting drift for all approved contracts")
    
    # Get all approved contracts
    all_contracts = list_contracts(status=ContractStatus.APPROVED)
    
    drift_reports = {}
    detector = DriftDetector()
    
    for contract_info in all_contracts:
        table_name = contract_info.get("table_name")
        if not table_name:
            continue
            
        try:
            # Load full contract
            from app.core.contract_storage import load_contract
            contract = load_contract(contract_info["contract_id"])
            
            # Detect drift
            drift_report = detector.detect_drift(
                table_name=table_name,
                contract=contract
            )
            
            drift_reports[table_name] = drift_report
            
        except Exception as e:
            logger.error(f"Failed to detect drift for {table_name}: {e}")
            continue
    
    logger.info(f"Drift detection complete for {len(drift_reports)} tables")
    return drift_reports


def get_drift_summary() -> Dict:
    """
    Get summary of drift status across all approved contracts.
    
    Returns:
        Dict with summary statistics
    """
    drift_reports = detect_drift_for_all_approved()
    
    summary = {
        "total_tables_monitored": len(drift_reports),
        "tables_with_drift": 0,
        "total_changes": 0,
        "by_severity": {
            "critical": 0,
            "warning": 0,
            "info": 0
        },
        "tables": []
    }
    
    for table_name, report in drift_reports.items():
        if report.drift_detected:
            summary["tables_with_drift"] += 1
            summary["total_changes"] += len(report.changes)
            
            # Count by severity
            for change in report.changes:
                severity = change.severity.value
                summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        summary["tables"].append({
            "table_name": table_name,
            "drift_detected": report.drift_detected,
            "change_count": len(report.changes),
            "contract_id": report.contract_id,
            "checked_at": report.checked_at.isoformat()
        })
    
    return summary


# Made with Bob