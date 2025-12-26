"""User Management view for AutoRBI application (CustomTkinter).

This view follows the same UI patterns as work_history.py and report_menu.py
to ensure consistent user experience across the application.
"""

from typing import List, Dict, Any, Optional, Callable
import customtkinter as ctk
from tkinter import messagebox

from AutoRBI_Database.validation_rules import (
    RoleRules,
    StatusRules,
    get_username_validation_error,
    get_fullname_validation_error,
    get_password_validation_error,
)


class UserManagementView:
    """Handles the User Management interface (Admin only)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.user_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None
        
        # Pagination state
        self.current_page = 1
        self.per_page = 25
        self.total_pages = 1
        self.total_users = 0
        
        # Filter state
        self.current_status_filter: Optional[str] = None
        self.current_role_filter: Optional[str] = None
        self.current_search: str = ""

        # Colors
        self.divider_color = ("gray80", "gray30")

    def _get_column_config(self, widget: ctk.CTkFrame):
        """Standardizes column widths and weights across header and body."""
        # Data Columns (indices 0, 2, 4, 6, 8, 10)
        widget.grid_columnconfigure(0, weight=1, minsize=50)   # No.
        widget.grid_columnconfigure(2, weight=2)               # Username
        widget.grid_columnconfigure(4, weight=3)               # Full Name
        widget.grid_columnconfigure(6, weight=2)               # Role
        widget.grid_columnconfigure(8, weight=2)               # Status
        widget.grid_columnconfigure(10, weight=2)              # Actions

        # Divider Columns (indices 1, 3, 5, 7, 9)
        for col in [1, 3, 5, 7, 9]:
            widget.grid_columnconfigure(col, weight=0, minsize=1)

    def _add_divider(self, parent, row, col):
        """Creates a thin vertical line to separate columns."""
        divider = ctk.CTkFrame(parent, width=1, height=30, fg_color=self.divider_color)
        divider.grid(row=row, column=col, sticky="ns", pady=8)

    def load_users(self, users: List[Dict[str, Any]], total: int = 0, total_pages: int = 1) -> None:
        """Populate the users table."""
        self.user_rows = users
        self.total_users = total
        self.total_pages = total_pages
        
        if self.table_body is not None:
            # Clear current rows
            for child in self.table_body.winfo_children():
                child.destroy()
            
            # Rebuild table body
            if users:
                for idx, user in enumerate(users, start=1):
                    self._add_user_row(idx, user)
            else:
                hint_label = ctk.CTkLabel(
                    self.table_body,
                    text="No users found matching the current filters.",
                    font=("Segoe UI", 11),
                    text_color=("gray40", "gray75"),
                )
                hint_label.grid(row=0, column=0, columnspan=11, sticky="w", pady=(20, 20), padx=20)
        
        self._update_pagination_display()

    def _add_user_row(self, index: int, user: Dict[str, Any]) -> None:
        """Add a row to the table with perfect alignment."""
        if self.table_body is None: return

        row_idx = index
        display_idx = (self.current_page - 1) * self.per_page + index

        # Column 0: No.
        ctk.CTkLabel(self.table_body, text=str(display_idx), font=("Segoe UI", 11), anchor="w").grid(row=row_idx, column=0, sticky="ew", padx=2 , pady=8)
        self._add_divider(self.table_body, row_idx, 1)

        # Column 2: Username
        ctk.CTkLabel(self.table_body, text=user.get("username", "-"), font=("Segoe UI", 12), anchor="w").grid(row=row_idx, column=2, sticky="ew", padx=(23, 0) , pady=8)
        self._add_divider(self.table_body, row_idx, 3)

        # Column 4: Full Name
        ctk.CTkLabel(self.table_body, text=user.get("full_name", "-"), font=("Segoe UI", 11), anchor="w").grid(row=row_idx, column=4, sticky="ew", padx=(75, 0), pady=8)
        self._add_divider(self.table_body, row_idx, 5)

        # Column 6: Role Badge
        role = user.get("role", "Engineer")
        role_colors = {"Admin": ("#3498db", "#2980b9"), "Engineer": ("gray70", "gray60")}
        role_badge = ctk.CTkLabel(self.table_body, text=role, font=("Segoe UI", 9, "bold"), 
                                 fg_color=role_colors.get(role, ("gray70", "gray60")), 
                                 corner_radius=4, width=90, height=24, anchor="center")
        role_badge.grid(row=row_idx, column=6, padx=12, pady=8)
        self._add_divider(self.table_body, row_idx, 7)

        # Column 8: Status Badge
        status = user.get("status", "Active")
        status_colors = {"Active": ("#2ecc71", "#27ae60"), "Inactive": ("#e74c3c", "#c0392b")}
        status_badge = ctk.CTkLabel(self.table_body, text=status, font=("Segoe UI", 9, "bold"), 
                                   fg_color=status_colors.get(status, ("gray70", "gray60")), 
                                   corner_radius=4, width=90, height=24, anchor="center")
        status_badge.grid(row=row_idx, column=8, padx=12, pady=8)
        self._add_divider(self.table_body, row_idx, 9)

        # Column 10: Actions
        actions_frame = ctk.CTkFrame(self.table_body, fg_color="transparent")
        actions_frame.grid(row=row_idx, column=10, sticky="e", padx=12 , pady=8)

        edit_btn = ctk.CTkButton(actions_frame, text="Edit", width=60, height=28, font=("Segoe UI", 9),
                                 command=lambda u=user: self._show_edit_dialog(u))
        edit_btn.pack(side="right", padx=(4, 0))

        if user.get("id") != self.controller.current_user.get("id"):
            is_active = status == "Active"
            toggle_btn = ctk.CTkButton(
                actions_frame, text="Deactivate" if is_active else "Activate",
                width=80, height=28, font=("Segoe UI", 9),
                fg_color=("gray20", "gray30") if is_active else ("#27ae60", "#1e8449"),
                hover_color=("red", "darkred") if is_active else ("#2ecc71", "#27ae60"),
                command=lambda u=user: self._toggle_user_status(u)
            )
            toggle_btn.pack(side="right")

    def show(self) -> None:
        """Display the User Management interface."""
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)
        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(header, text="← Back to Main Menu", command=self.controller.show_main_menu,
                                width=180, height=32, font=("Segoe UI", 10), fg_color="transparent",
                                text_color=("gray20", "gray90"), hover_color=("gray85", "gray30"))
        back_btn.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="AutoRBI", font=("Segoe UI", 24, "bold")).grid(row=0, column=1, sticky="e")

        # Main Panel
        main_frame = ctk.CTkFrame(root_frame, corner_radius=18, border_width=1, border_color=("gray80", "gray25"))
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        main_frame.grid_rowconfigure(3, weight=1) 
        main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_frame, text="User Management", font=("Segoe UI", 26, "bold")).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        # Subtitle & Add Button
        subtitle_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        subtitle_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        ctk.CTkLabel(subtitle_frame, text="Manage user accounts, roles, and access permissions.", font=("Segoe UI", 11), text_color=("gray25", "gray80")).pack(side="left")
        ctk.CTkButton(subtitle_frame, text="+ Add User", command=self._show_add_dialog, width=120, height=32, font=("Segoe UI", 10, "bold")).pack(side="right")

        # Filters
        filter_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        filter_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))

        ctk.CTkLabel(filter_section, text="Status:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        self.status_filter_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_section, values=["All", "Active", "Inactive"], variable=self.status_filter_var, width=100, height=28, state="readonly").pack(side="left", padx=(0, 16))

        ctk.CTkLabel(filter_section, text="Role:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        self.role_filter_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_section, values=["All"] + RoleRules.VALID_ROLES, variable=self.role_filter_var, width=100, height=28, state="readonly").pack(side="left", padx=(0, 16))

        self.search_entry = ctk.CTkEntry(filter_section, placeholder_text="Search user...", width=180, height=28)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._apply_filters())

        ctk.CTkButton(filter_section, text="Apply", command=self._apply_filters, width=70, height=28).pack(side="left", padx=(0, 4))
        ctk.CTkButton(filter_section, text="Clear", command=self._clear_filters, width=70, height=28, fg_color=("gray20", "gray30")).pack(side="left")

        # Table
        table_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_container.grid(row=3, column=0, sticky="nsew", padx=0, pady=(0, 12))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(table_container, corner_radius=8, border_width=1, border_color=("gray80", "gray30"), fg_color=("gray90", "gray20"))
        header_row.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=0)
        self._get_column_config(header_row)

        # No.
        ctk.CTkLabel(
            header_row,
            text="No.",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=(16, 20), pady=8)
        self._add_divider(header_row, 0, 1)

        # Username
        ctk.CTkLabel(
            header_row,
            text="Username",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).grid(row=0, column=2, sticky="ew", padx=(12, 50), pady=8)
        self._add_divider(header_row, 0, 3)

        # Full Name
        ctk.CTkLabel(
            header_row,
            text="Full Name",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).grid(row=0, column=4, sticky="w", padx=(2, 2), pady=8)
        self._add_divider(header_row, 0, 5)

        # Role
        ctk.CTkLabel(
            header_row,
            text="Role",
            font=("Segoe UI", 11, "bold"),
            anchor="center"
        ).grid(row=0, column=6, sticky="ew", padx=(2, 30), pady=8)
        self._add_divider(header_row, 0, 7)

        # Status
        ctk.CTkLabel(
            header_row,
            text="Status",
            font=("Segoe UI", 11, "bold"),
            anchor="center"
        ).grid(row=0, column=8, sticky="ew", padx=(2, 100), pady=8)
        self._add_divider(header_row, 0, 9)

        # Actions
        ctk.CTkLabel(
            header_row,
            text="Actions",
            font=("Segoe UI", 11, "bold"),
            anchor="center"
        ).grid(row=0, column=10, sticky="ew", padx=(8, 16), pady=8)


        self.table_body = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_body.grid(row=1, column=0, sticky="nsew", padx=(20, 0), pady=0)
        self._get_column_config(self.table_body)

        # Pagination
        pagination_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pagination_frame.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 18))
        pagination_frame.grid_rowconfigure(0, weight=1)
        pagination_frame.grid_columnconfigure(0, weight=1)

        self.pagination_info = ctk.CTkLabel(pagination_frame, text="Loading...", font=("Segoe UI", 10), text_color=("gray40", "gray75"))
        self.pagination_info.grid(row=0, column=0, sticky="w")

        nav_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        nav_frame.grid_columnconfigure(1, weight=1)  # Center the label

        self.prev_btn = ctk.CTkButton(nav_frame, text="← Previous", command=self._prev_page, width=90, height=28, state="disabled")
        self.prev_btn.grid(row=0, column=0, padx=(0, 8))
        self.page_label = ctk.CTkLabel(nav_frame, text="Page 1 of 1", font=("Segoe UI", 10))
        self.page_label.grid(row=0, column=1)
        self.next_btn = ctk.CTkButton(nav_frame, text="Next →", command=self._next_page, width=90, height=28, state="disabled")
        self.next_btn.grid(row=0, column=2, padx=(8, 0))

        self._refresh_users()

    def _refresh_users(self) -> None:
        result = self.controller.get_users_list(status_filter=self.current_status_filter, role_filter=self.current_role_filter,
                                             search_query=self.current_search, page=self.current_page, per_page=self.per_page)
        if result.get("success"):
            self.load_users(users=result.get("users", []), total=result.get("total", 0), total_pages=result.get("total_pages", 1))
        else:
            messagebox.showerror("Error", result.get("message", "Failed to load users"))

    def _apply_filters(self):
        self.current_status_filter = None if self.status_filter_var.get() == "All" else self.status_filter_var.get()
        self.current_role_filter = None if self.role_filter_var.get() == "All" else self.role_filter_var.get()
        self.current_search = self.search_entry.get().strip()
        self.current_page = 1
        self._refresh_users()

    def _clear_filters(self):
        self.status_filter_var.set("All")
        self.role_filter_var.set("All")
        self.search_entry.delete(0, "end")
        self._apply_filters()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_users()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_users()
            

    def _update_pagination_display(self):
        if not hasattr(self, 'pagination_info'): return
        start = (self.current_page - 1) * self.per_page + 1
        end = min(self.current_page * self.per_page, self.total_users)
        self.pagination_info.configure(text=f"Showing {start}-{end} of {self.total_users} users" if self.total_users > 0 else "No users found")
        self.page_label.configure(text=f"Page {self.current_page} of {self.total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")

    def _toggle_user_status(self, user):
        action = "deactivate" if user["status"] == "Active" else "activate"
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action} '{user['username']}'?"):
            result = self.controller.toggle_user_status(user["id"])
            if result.get("success"):
                messagebox.showinfo("Success", result["message"])
                self._refresh_users()

    def _show_edit_dialog(self, user):
        UserFormDialog(self.parent, self.controller, "edit", user, self._refresh_users)

    def _show_add_dialog(self):
        UserFormDialog(self.parent, self.controller, "add", None, self._refresh_users)


class UserFormDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a user."""
    
    def __init__(self, parent, controller, mode="add", user_data=None, on_save=None):
        super().__init__(parent)
        self.controller, self.mode, self.user_data, self.on_save = controller, mode, user_data or {}, on_save
        
        self.title("Add User" if mode == "add" else "Edit User")
        self.geometry("450x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_form()

    def _create_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(container, text="Create New User" if self.mode == "add" else "Edit User Details", font=("Segoe UI", 18, "bold")).pack(pady=(0, 20))

        form = ctk.CTkFrame(container, fg_color="transparent")
        form.pack(fill="x")

        if self.mode == "add":
            ctk.CTkLabel(form, text="Username:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            self.username_entry = ctk.CTkEntry(form, height=36)
            self.username_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Full Name:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.fullname_entry = ctk.CTkEntry(form, height=36)
        self.fullname_entry.pack(fill="x", pady=(0, 16))
        if self.mode == "edit": self.fullname_entry.insert(0, self.user_data.get("full_name", ""))

        ctk.CTkLabel(form, text="Role:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.role_var = ctk.StringVar(value=self.user_data.get("role", RoleRules.DEFAULT_ROLE))
        ctk.CTkComboBox(form, values=RoleRules.VALID_ROLES, variable=self.role_var, height=36, state="readonly").pack(fill="x", pady=(0, 16))

        # Password Logic
        self.pw_frame = ctk.CTkFrame(form, fg_color="transparent")
        if self.mode == "add":
            self.pw_frame.pack(fill="x")
        else:
            self.reset_pw_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(form, text="Reset Password", variable=self.reset_pw_var, command=self._toggle_pw).pack(anchor="w", pady=8)

        ctk.CTkLabel(self.pw_frame, text="Password:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.password_entry = ctk.CTkEntry(self.pw_frame, height=36, show="•")
        self.password_entry.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(self.pw_frame, text="Confirm Password:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.confirm_entry = ctk.CTkEntry(self.pw_frame, height=36, show="•")
        self.confirm_entry.pack(fill="x")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="transparent", text_color=("gray20", "gray90")).pack(side="left")
        ctk.CTkButton(btn_frame, text="Save", command=self._save, width=120).pack(side="right")

    def _toggle_pw(self):
        if self.reset_pw_var.get(): self.pw_frame.pack(fill="x")
        else: self.pw_frame.pack_forget()

    def _save(self):
        full_name = self.fullname_entry.get().strip()
        role = self.role_var.get()
        
        if self.mode == "add":
            username = self.username_entry.get().strip()
            password = self.password_entry.get()
            if password != self.confirm_entry.get():
                return messagebox.showerror("Error", "Passwords do not match")
            result = self.controller.create_new_user(username, full_name, password, role)
        else:
            pw = self.password_entry.get() if self.reset_pw_var.get() else None
            result = self.controller.update_user(self.user_data["id"], full_name, role, pw)

        if result.get("success"):
            messagebox.showinfo("Success", result["message"])
            if self.on_save: self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", result.get("message"))