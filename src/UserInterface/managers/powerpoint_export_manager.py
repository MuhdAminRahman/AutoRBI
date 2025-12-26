"""
PowerPoint Export Manager
"""

from powerpoint_generator import PowerPointGenerator
import os


class PowerPointExportManager:
    def __init__(self, project_root, state, controller, executor, log_callback, parent_window):
        self.project_root = project_root
        self.state = state
        self.controller = controller
        self.executor = executor
        self.log_callback = log_callback
        self.parent_window = parent_window

    def export_to_powerpoint(self):
        # Get template path, perhaps from state or config
        template_path = os.path.join(self.project_root, "templates", "Inspection_Plan_Template.pptx")  # Assuming
        if not os.path.exists(template_path):
            self.log_callback("PowerPoint template not found")
            return

        generator = PowerPointGenerator(template_path, self.log_callback)
        # Assuming state has equipment_map
        if hasattr(self.state, 'equipment_map'):
            output_path = os.path.join(self.project_root, "output", "Inspection_Plan.pptx")
            success = generator.generate_from_equipment_map(self.state.equipment_map, output_path)
            if success:
                self.log_callback(f"PowerPoint exported to {output_path}")
                # Update work with ppt path
                if hasattr(self.controller, 'update_work_ppt_path'):
                    self.controller.update_work_ppt_path(self.state.work_id, output_path)
            else:
                self.log_callback("Failed to export PowerPoint")
        else:
            self.log_callback("No equipment data to export")