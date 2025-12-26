"""
Database Service - Wrapper for database operations
"""

from AutoRBI_Database.database.crud import (
    create_history,
    create_equipment,
    get_equipment_by_no,
    get_equipment_by_work,
    create_correction_log,
    get_component_by_id,
)
from AutoRBI_Database.services.correction_service import apply_corrections
from AutoRBI_Database.database.models import Component


class DatabaseService:
    @staticmethod
    def log_work_history(db, work_id, user_id, action_type, description):
        return create_history(db, work_id, user_id, action_type, description)

    @staticmethod
    def batch_save_equipment(db, work_id, user_id, updated_map, drawing_paths):
        # updated_map is dict of equipment_number: data
        success = 0
        failures = 0
        for eq_no, data in updated_map.items():
            try:
                drawing_path = drawing_paths.get(eq_no)
                equipment = create_equipment(db, work_id, eq_no, data.get('pmt_no'), data.get('description'))
                if drawing_path:
                    # Assuming update_drawing_path exists
                    from AutoRBI_Database.database.crud import update_drawing_path
                    update_drawing_path(db, equipment.equipment_id, drawing_path)
                success += 1
            except:
                failures += 1
        return success, failures

    @staticmethod
    def get_equipment_id_by_equipment_number(db, work_id, equipment_number):
        equipment = get_equipment_by_no(db, work_id, equipment_number)
        return equipment.equipment_id if equipment else None

    @staticmethod
    def get_equipment_by_work_and_number(db, work_id, equipment_number):
        return get_equipment_by_no(db, work_id, equipment_number)

    @staticmethod
    def count_correction_fields(orig_comp, existing_data):
        # Count fields to fill and corrected
        tracked_fields = [
            "fluid", "material_spec", "material_grade", "insulation",
            "design_temp", "design_pressure", "operating_temp", "operating_pressure"
        ]
        to_fill = sum(1 for field in tracked_fields if getattr(orig_comp, field, None) in [None, ""])
        corrected = sum(1 for field in tracked_fields if getattr(orig_comp, field, None) in [None, ""] and existing_data.get(field) not in [None, ""])
        return to_fill, corrected

    @staticmethod
    def log_correction(db, equipment_id, user_id, fields_corrected, total_fields):
        return create_correction_log(db, equipment_id, user_id, fields_corrected, total_fields)