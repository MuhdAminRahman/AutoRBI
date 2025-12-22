import os
from typing import List, Optional
from tkinter import filedialog, messagebox

class FileService:
    """Handles all file-related operations"""
    
    def __init__(self, pdf_converter, log_callback: Optional[callable] = None):
        self.pdf_converter = pdf_converter
        self.log_callback = log_callback or print
    
    def select_files(self, mode: str = "single") -> List[str]:
        """Open file dialog and return selected PDF files"""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        
        try:
            if mode == "single":
                path = filedialog.askopenfilename(filetypes=filetypes)
                return [path] if path else []
            
            elif mode == "multiple":
                paths = filedialog.askopenfilenames(filetypes=filetypes)
                return list(paths) if paths else []
            
            elif mode == "folder":
                folder = filedialog.askdirectory(title="Select folder containing PDF files")
                if folder:
                    return self.find_pdfs_in_folder(folder)
                return []
        
        except Exception as e:
            self.log_callback(f"❌ File selection error: {e}")
            return []
    
    def find_pdfs_in_folder(self, folder_path: str) -> List[str]:
        """Find all PDF files in a folder recursively"""
        pdf_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files
    
    def convert_pdfs_to_images(self, pdf_paths: List[str]) -> List[str]:
        """Convert PDF files to images and return equipment numbers"""
        all_converted = []
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                self.log_callback(f"⚠️ PDF not found: {os.path.basename(pdf_path)}")
                continue
            
            filename = os.path.basename(pdf_path)
            self.log_callback(f"📄 Converting PDF: {filename}")
            
            try:
                image_paths = self.pdf_converter.convert_single(pdf_path)
                
                if image_paths:
                    from data_extractor.utils import get_equipment_number_from_image_path
                    for img_path in image_paths:
                        equip_no = get_equipment_number_from_image_path(img_path)
                        self.log_callback(f"    - Equipment No.: {equip_no}")
                        all_converted.append(equip_no)
                    
                    self.log_callback(f"  ✅ Created {len(image_paths)} image(s)")
                else:
                    self.log_callback(f"  ❌ Failed to convert {filename}")
            
            except Exception as e:
                self.log_callback(f"  ❌ Error: {str(e)}")
        
        return all_converted
    
    def get_work_excel_path(self, work_id: str, project_root: str) -> Optional[str]:
        """Get path to Excel file for a work"""
        try:
            excel_dir = os.path.join(project_root, "src", "output_files", work_id, "excel", "updated")
            default_dir = os.path.join(project_root, "src", "output_files", work_id, "excel", "default")

            # First check the updated directory
            if os.path.isdir(excel_dir):
                for fname in os.listdir(excel_dir):
                    if fname.lower().endswith(('.xlsx', '.xls')):
                        return os.path.join(excel_dir, fname)

            # If no Excel files found in updated, check default directory
            if os.path.isdir(default_dir):
                for fname in os.listdir(default_dir):
                    if fname.lower().endswith(('.xlsx', '.xls')):
                        return os.path.join(default_dir, fname)
            
        except Exception:
            pass
        return None