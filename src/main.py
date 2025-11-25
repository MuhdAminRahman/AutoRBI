"""Main entry point for AutoRBI application."""
import logging
#from data_extractor import MasterfileExtractor
#from excel_manager import ExcelManager
from app import AutoRBIApp
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main() -> None:
    """Run the AutoRBI application."""
    app = AutoRBIApp()
    app.mainloop()
    #test_DataExtractor()


if __name__ == "__main__":
    main()

