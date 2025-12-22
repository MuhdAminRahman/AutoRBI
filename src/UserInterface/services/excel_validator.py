from dataclasses import dataclass
from enum import Enum
import os
from typing import Optional, Set, Tuple


class ExcelFileType(Enum):
    """Types of Excel files"""
    DEFAULT = "default"      # No work done yet
    UPDATED = "updated"      # Work in progress
    NOT_FOUND = "not_found"  # No file exists


@dataclass
class ExcelFileInfo:
    """Information about Excel file status"""
    file_type: ExcelFileType
    file_path: Optional[str]
    has_work_done: bool
    equipment_with_work: Set[str]  # Equipment numbers that have work done
    last_modified: Optional[float]


class ExcelValidator:
    """Validates Excel files and work status"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
    
    def get_excel_file_info(self, work_id: str) -> ExcelFileInfo:
        """
        Get information about Excel file for a work.
        Checks both default and updated locations.
        """
        base_path = os.path.join(self.project_root, "src", "output_files", work_id, "excel")
        
        # Check for updated file first (work in progress)
        updated_path = os.path.join(base_path, "updated")
        updated_file = self._find_excel_file(updated_path)
        
        if updated_file:
            equipment_with_work = self._get_equipment_with_work(updated_file)
            return ExcelFileInfo(
                file_type=ExcelFileType.UPDATED,
                file_path=updated_file,
                has_work_done=len(equipment_with_work) > 0,
                equipment_with_work=equipment_with_work,
                last_modified=os.path.getmtime(updated_file)
            )
        
        # Check for default file
        default_path = os.path.join(base_path, "default")
        default_file = self._find_excel_file(default_path)
        
        if default_file:
            return ExcelFileInfo(
                file_type=ExcelFileType.DEFAULT,
                file_path=default_file,
                has_work_done=False,
                equipment_with_work=set(),
                last_modified=os.path.getmtime(default_file)
            )
        
        # No file found
        return ExcelFileInfo(
            file_type=ExcelFileType.NOT_FOUND,
            file_path=None,
            has_work_done=False,
            equipment_with_work=set(),
            last_modified=None
        )
    
    def _find_excel_file(self, directory: str) -> Optional[str]:
        """Find Excel file in directory"""
        if not os.path.isdir(directory):
            return None
        
        for fname in os.listdir(directory):
            if fname.lower().endswith(('.xlsx', '.xls')):
                return os.path.join(directory, fname)
        
        return None
    
    def _get_equipment_with_work(self, excel_path: str) -> Set[str]:
        """
        Get set of equipment numbers that have work done.
        Work is considered "done" if specific fields are filled.
        """
        equipment_with_work = set()
        
        try:
            from excel_manager import ExcelManager
            manager = ExcelManager(excel_path)
            equipment_map = manager.read_masterfile()
            
            # Check each equipment for completed work
            for eq_no, equipment in equipment_map.items():
                if self._has_completed_work(equipment):
                    equipment_with_work.add(eq_no)
        
        except Exception as e:
            print(f"Error reading Excel file: {e}")
        
        return equipment_with_work
    
    def _has_completed_work(self, equipment) -> bool:
        """Check if equipment has any completed work"""
        for component in equipment.components:
            # Check if critical fields are filled
            critical_fields = ['fluid', 'type', 'spec', 'grade']
            filled_count = sum(
                1 for field in critical_fields
                if component.get_existing_data_value(field)
            )
            
            # If at least 2 critical fields are filled, consider it as work done
            if filled_count >= 2:
                return True
        
        return False
    
    def can_upload_equipment(
        self, 
        excel_file_info: ExcelFileInfo,
        equipment_number: str
    ) -> Tuple[bool, str]:
        """
        Check if equipment can be uploaded (no work done yet).
        
        Returns:
            (can_upload, reason)
        """
        if excel_file_info.file_type == ExcelFileType.NOT_FOUND:
            return False, "No Excel file found. Please upload default file first."
        
        if equipment_number in excel_file_info.equipment_with_work:
            return False, f"Equipment {equipment_number} already has work done. Cannot re-upload."
        
        return True, "OK"