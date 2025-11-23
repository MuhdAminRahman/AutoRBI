"""Main application class for AutoRBI."""

import tkinter as tk
from tkinter import messagebox

try:
    # Try relative imports (when run as module)
    from . import styles
    from .views import (
        AnalyticsView,
        LoginView,
        MainMenuView,
        NewWorkView,
        RegistrationView,
        ReportMenuView,
        WorkHistoryView,
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    import styles
    from views import (
        AnalyticsView,
        LoginView,
        MainMenuView,
        NewWorkView,
        RegistrationView,
        ReportMenuView,
        WorkHistoryView,
    )


class AutoRBIApp(tk.Tk):
    
    def __init__(self):
        super().__init__()
        self.title("AutoRBI")
        self.geometry("1000x700")
        self.minsize(900, 650)
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure styles
        styles.configure_styles(self)
        
        # Initialize views
        self.login_view = LoginView(self, self)
        self.registration_view = RegistrationView(self, self)
        self.main_menu_view = MainMenuView(self, self)
        self.new_work_view = NewWorkView(self, self)
        self.report_menu_view = ReportMenuView(self, self)
        self.work_history_view = WorkHistoryView(self, self)
        self.analytics_view = AnalyticsView(self, self)
        
        # Show login screen initially
        self.show_login()
    
    # Navigation methods
    def show_login(self) -> None:
        """Show the login view."""
        self.login_view.show()
    
    def show_registration(self) -> None:
        """Show the registration view."""
        self.registration_view.show()
    
    def show_main_menu(self) -> None:
        """Show the main menu view."""
        self.main_menu_view.show()
    
    def show_new_work(self) -> None:
        """Show the New Work view."""
        self.new_work_view.show()
    
    def show_report_menu(self) -> None:
        """Show the Report Menu view."""
        self.report_menu_view.show()
    
    def show_work_history(self) -> None:
        """Show the Work History Menu view."""
        self.work_history_view.show()
    
    def show_analytics(self) -> None:
        """Show the Analytics Dashboard view."""
        self.analytics_view.show()
    
    def logout(self) -> None:
        """Handle logout and return to login screen."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.show_login()

