"""Main menu view for AutoRBI application (CustomTkinter)."""

import os
from datetime import datetime
from typing import Optional

from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil


class MainMenuView:
    """Handles the main menu interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._logo_image: Optional[ctk.CTkImage] = self._load_logo()
        self._datetime_label: Optional[ctk.CTkLabel] = None
        self.profile_dropdown_open = False
        self.search_results_frame: Optional[ctk.CTkFrame] = None
        # Analytics attributes
        self.current_period = "all_time"
        self.kpi_cards = {}

    def _load_logo(self) -> Optional[ctk.CTkImage]:
        """Load the iPETRO logo from disk if available."""
        try:
            base_dir = os.path.dirname(__file__)
            logo_path = os.path.join(base_dir, "ipetro.png")
            image = Image.open(logo_path)
            return ctk.CTkImage(image, size=(150, 32))
        except Exception:
            return None

    def _update_datetime(self) -> None:
        """Update the datetime label every second."""
        # Ensure label still exists before updating (may be destroyed when navigating)
        try:
            if self._datetime_label is None or not self._datetime_label.winfo_exists():
                return
        except Exception:
            return

        try:
            now = datetime.now().strftime("%d %b %Y  •  %I:%M:%S %p")
            # Double-check widget exists before configuring
            if not self._datetime_label.winfo_exists():
                return
            self._datetime_label.configure(text=now)
        except Exception:
            # Protect against TclError if widget was destroyed between checks
            return

        # Schedule next update only if parent window still exists
        try:
            if hasattr(self.parent, "winfo_exists") and self.parent.winfo_exists():
                self.parent.after(1000, self._update_datetime)
        except Exception:
            pass

    def show(self) -> None:
        """Display the main menu interface."""

        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Get current user data from controller
        user = self.controller.current_user

        # Extract user info with fallbacks
        full_name = user.get("full_name") or user.get("username") or "Unknown User"
        username = user.get("username") or "unknown"

        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Root content frame
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with logo, search, datetime, profile, and logout
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=0)  # logo
        header.grid_columnconfigure(1, weight=1)  # search
        header.grid_columnconfigure(2, weight=0)  # datetime
        header.grid_columnconfigure(3, weight=0)  # profile/logout

        # Left side: logo on top, small title below
        logo_block = ctk.CTkFrame(header, fg_color="transparent")
        logo_block.grid(row=0, column=0, sticky="w")

        if self._logo_image is not None:
            logo_label = ctk.CTkLabel(
                logo_block,
                text="",
                image=self._logo_image,
            )
            logo_label.pack(anchor="w")

        # Search bar (center)
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="ew", padx=20)

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search work history, reports, equipment...",
            font=("Segoe UI", 11),
            height=36,
            corner_radius=18,
        )
        search_entry.pack(fill="x", expand=True)
        search_entry.bind(
            "<KeyRelease>", lambda e: self._handle_search(search_entry.get())
        )

        # Search results dropdown (initially hidden)
        self.search_results_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("white", "gray20"),
        )

        # Center/right: larger date & time
        self._datetime_label = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI", 14, "bold"),
            text_color=("gray85", "gray90"),
        )
        self._datetime_label.grid(row=0, column=2, sticky="e", padx=(0, 20))
        self._update_datetime()

        # User profile section (right side)
        profile_section = ctk.CTkFrame(header, fg_color="transparent")
        profile_section.grid(row=0, column=3, sticky="e")

        # Username label (optional - can be hidden)
        username_label = ctk.CTkLabel(
            profile_section,
            text=full_name,  # TODO: Backend - Get from backend
            font=("Segoe UI", 11),
            text_color=("gray60", "gray80"),
        )
        username_label.pack(side="left", padx=(0, 10))

        # Circular profile avatar frame
        avatar_frame = ctk.CTkFrame(
            profile_section,
            width=44,
            height=44,
            corner_radius=22,  # Perfect circle (half of width/height)
            fg_color=("gray80", "gray30"),
            border_width=2,
            border_color=("gray70", "gray40"),
        )
        avatar_frame.pack(side="left", padx=(0, 8))

        def on_avatar_click(e):
            """Handle avatar click - stop event propagation."""
            e.widget.focus_set()
            self._toggle_profile_dropdown()
            return "break"  # Stop event propagation

        avatar_frame.bind("<Button-1>", on_avatar_click)

        # Avatar icon/label inside circle
        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="👤",
            font=("Segoe UI", 20),
            fg_color="transparent",
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")
        avatar_label.bind("<Button-1>", on_avatar_click)

        # Make the frame clickable with hover effect
        def on_enter(e):
            avatar_frame.configure(
                fg_color=("gray75", "gray35"), border_color=("gray65", "gray45")
            )

        def on_leave(e):
            avatar_frame.configure(
                fg_color=("gray80", "gray30"), border_color=("gray70", "gray40")
            )

        for widget in [avatar_frame, avatar_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        # Profile dropdown menu (initially hidden)
        self.profile_dropdown = ctk.CTkFrame(
            root_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("white", "gray20"),
            width=200,
        )
        # Initially hide the dropdown
        self.profile_dropdown.place_forget()

        # Logout button
        logout_btn = ctk.CTkButton(
            profile_section,
            text="Logout",
            command=self.controller.logout,
            width=100,
            height=36,
            font=("Segoe UI", 10, "bold"),
        )
        logout_btn.pack(side="left")

        # Store reference to profile section for click detection (after widgets are created)
        self.profile_section_ref = profile_section
        self.avatar_frame_ref = avatar_frame
        self.avatar_label_ref = avatar_label

        # Bind click outside to close dropdowns (use after a delay to allow dropdown to show)
        def delayed_click_handler(event):
            # Only check for outside clicks if dropdown is open
            if self.profile_dropdown_open:
                self.parent.after(100, lambda: self._handle_click_outside(event))

        root_frame.bind("<Button-1>", delayed_click_handler)

        # Main content area
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        main_frame.grid_columnconfigure(0, weight=1)

        # Analytics Dashboard Content (with scrolling for admin section)
        main_frame.grid_rowconfigure(0, weight=1)  # Make scrollable area expand

        scroll_container = ctk.CTkScrollableFrame(
            main_frame,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
        )
        scroll_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        analytics_frame = scroll_container
        analytics_frame.grid_columnconfigure(0, weight=1)

        # Analytics Dashboard title and Work History button row
        title_frame = ctk.CTkFrame(analytics_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(18, 6))
        title_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            title_frame,
            text="Analytics Dashboard",
            font=("Segoe UI", 24, "bold"),
            anchor="w",
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24)

        # Work History button at the top right of analytics section
        work_history_btn = ctk.CTkButton(
            title_frame,
            text="📋 Work History",
            command=self.controller.show_work_history,
            width=120,
            height=32,
            font=("Segoe UI", 10),
            fg_color=("#1B9751", "#1B9751"),  # Green colors
            hover_color=("#228B22", "#228B22"),  # Darker green on hover
        )
        work_history_btn.grid(row=0, column=1, sticky="e", padx=(0, 24))

        subtitle_label = ctk.CTkLabel(
            analytics_frame,
            text="Monitor performance metrics and extraction statistics.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # Period selector buttons
        period_section = ctk.CTkFrame(analytics_frame, fg_color="transparent")
        period_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))

        period_label = ctk.CTkLabel(
            period_section,
            text="Time period:",
            font=("Segoe UI", 10, "bold"),
        )
        period_label.pack(side="left", padx=(0, 8))

        period_buttons = [
            ("All time", "all_time"),
            ("Last month", "last_month"),
            ("Last week", "last_week"),
            ("Today", "today"),
        ]
        for label, period_key in period_buttons:
            btn = ctk.CTkButton(
                period_section,
                text=label,
                width=100,
                height=28,
                font=("Segoe UI", 9),
                fg_color=("gray20", "gray30") if getattr(self, 'current_period', 'all_time') != period_key else None,
                command=lambda p=period_key: self._change_period(p),
            )
            btn.pack(side="left", padx=(0, 6))

        # KPI cards row
        kpi_section = ctk.CTkFrame(analytics_frame, fg_color="transparent")
        kpi_section.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 18))
        kpi_section.grid_columnconfigure(0, weight=1)
        kpi_section.grid_columnconfigure(1, weight=1)
        kpi_section.grid_columnconfigure(2, weight=1)
        kpi_section.grid_columnconfigure(3, weight=1)

        self._create_kpi_card(kpi_section, "Total Works", "0", "total_works_card", 0, 0)
        self._create_kpi_card(kpi_section, "Success Rate", "0%", "success_rate_card", 0, 1)
        self._create_kpi_card(kpi_section, "Avg Time", "0s", "avg_time_card", 0, 2)
        self._create_kpi_card(kpi_section, "Total Files", "0", "total_files_card", 0, 3)

        # Charts section (2 columns)
        charts_section = ctk.CTkFrame(analytics_frame, fg_color="transparent")
        charts_section.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 18))
        charts_section.grid_columnconfigure(0, weight=1)
        charts_section.grid_columnconfigure(1, weight=1)

        # Chart 1: Works over time
        chart1_card = ctk.CTkFrame(
            charts_section,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        chart1_card.grid(row=0, column=0, padx=(0, 8), pady=8, sticky="nsew")
        chart1_card.grid_columnconfigure(0, weight=1)
        chart1_card.grid_rowconfigure(1, weight=1)

        chart1_title = ctk.CTkLabel(
            chart1_card,
            text="Works Over Time",
            font=("Segoe UI", 12, "bold"),
        )
        chart1_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        chart1_placeholder = ctk.CTkLabel(
            chart1_card,
            text="[Chart placeholder]\nTime series visualization\nwill be rendered here.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            justify="center",
        )
        chart1_placeholder.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Chart 2: Status distribution
        chart2_card = ctk.CTkFrame(
            charts_section,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        chart2_card.grid(row=0, column=1, padx=(8, 0), pady=8, sticky="nsew")
        chart2_card.grid_columnconfigure(0, weight=1)
        chart2_card.grid_rowconfigure(1, weight=1)

        chart2_title = ctk.CTkLabel(
            chart2_card,
            text="Status Distribution",
            font=("Segoe UI", 12, "bold"),
        )
        chart2_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        chart2_placeholder = ctk.CTkLabel(
            chart2_card,
            text="[Chart placeholder]\nPie/bar chart showing\nstatus breakdown.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            justify="center",
        )
        chart2_placeholder.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Summary statistics card
        summary_card = ctk.CTkFrame(
            analytics_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        summary_card.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 24))

        summary_title = ctk.CTkLabel(
            summary_card,
            text="Recent Activity Summary",
            font=("Segoe UI", 12, "bold"),
        )
        summary_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        summary_content = ctk.CTkLabel(
            summary_card,
            text="• Most active day: N/A\n• Peak extraction time: N/A\n• Most processed file type: N/A",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            anchor="w",
            justify="left",
        )
        summary_content.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))

        # Bottom action buttons (New Work and Report Menu) - with descriptions like previous cards
        bottom_buttons_frame = ctk.CTkFrame(analytics_frame, fg_color="transparent")
        bottom_buttons_frame.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 24))
        bottom_buttons_frame.grid_columnconfigure(0, weight=1)
        bottom_buttons_frame.grid_columnconfigure(1, weight=1)

        # New Work card
        new_work_card = ctk.CTkFrame(
            bottom_buttons_frame,
            corner_radius=16,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        new_work_card.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        new_work_card.grid_rowconfigure(1, weight=1)
        new_work_card.grid_columnconfigure(0, weight=1)

        # New Work card title with separate icon and text for proper alignment
        new_work_title_frame = ctk.CTkFrame(new_work_card, fg_color="transparent")
        new_work_title_frame.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))
        new_work_title_frame.grid_columnconfigure(1, weight=1)

        new_work_icon = ctk.CTkLabel(
            new_work_title_frame,
            text="📁",
            font=("Segoe UI", 15),
            anchor="w",
        )
        new_work_icon.grid(row=0, column=0, sticky="w", padx=(0, 6))

        new_work_title = ctk.CTkLabel(
            new_work_title_frame,
            text="New Work",
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        )
        new_work_title.grid(row=0, column=1, sticky="w")

        new_work_desc = ctk.CTkLabel(
            new_work_card,
            text="Create and manage new work items.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
            anchor="w",
            justify="left",
            wraplength=200,
        )
        new_work_desc.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 10))

        new_work_btn = ctk.CTkButton(
            new_work_card,
            text="Open",
            command=self.controller.show_new_work,
            height=32,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#1f5f89"),
        )
        new_work_btn.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

        # Report Menu card
        report_card = ctk.CTkFrame(
            bottom_buttons_frame,
            corner_radius=16,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        report_card.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")
        report_card.grid_rowconfigure(1, weight=1)
        report_card.grid_columnconfigure(0, weight=1)

        # Report Menu card title with separate icon and text for proper alignment
        report_title_frame = ctk.CTkFrame(report_card, fg_color="transparent")
        report_title_frame.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))
        report_title_frame.grid_columnconfigure(1, weight=1)

        report_icon = ctk.CTkLabel(
            report_title_frame,
            text="📊",
            font=("Segoe UI", 15),
            anchor="w",
        )
        report_icon.grid(row=0, column=0, sticky="w", padx=(0, 6))

        report_title = ctk.CTkLabel(
            report_title_frame,
            text="Report Menu",
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        )
        report_title.grid(row=0, column=1, sticky="w")

        report_desc = ctk.CTkLabel(
            report_card,
            text="Generate and review reports.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
            anchor="w",
            justify="left",
            wraplength=200,
        )
        report_desc.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 10))

        report_btn = ctk.CTkButton(
            report_card,
            text="Open",
            command=self.controller.show_report_menu,
            height=32,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#1f5f89"),
        )
        report_btn.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

        # ================================================================
        # ADMIN SECTION (Only visible to admins)
        # ================================================================

        current_user_role = self.controller.current_user.get("role")

        if current_user_role == "Admin":
            # Admin section separator
            admin_separator = ctk.CTkFrame(
                analytics_frame,
                height=2,
                fg_color=("gray80", "gray30"),
            )
            admin_separator.grid(row=7, column=0, sticky="ew", padx=24, pady=(20, 10))

            # Admin label
            admin_label = ctk.CTkLabel(
                analytics_frame,
                text="Administration",
                font=("Segoe UI", 12, "bold"),
                text_color=("gray50", "gray70"),
            )
            admin_label.grid(row=8, column=0, sticky="w", padx=24, pady=(0, 8))

            # Admin management card
            admin_card = ctk.CTkFrame(
                analytics_frame,
                corner_radius=16,
                border_width=1,
                border_color=("#3498db", "#2980b9"),  # Blue border for admin card
            )
            admin_card.grid(row=9, column=0, sticky="ew", padx=24, pady=(0, 24))

            admin_card.grid_rowconfigure(1, weight=1)
            admin_card.grid_columnconfigure(0, weight=1)

            admin_title_lbl = ctk.CTkLabel(
                admin_card,
                text="👥 User Management",
                font=("Segoe UI", 15, "bold"),
                anchor="w",
            )
            admin_title_lbl.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))

            admin_desc_lbl = ctk.CTkLabel(
                admin_card,
                text="Manage user accounts, roles, and access permissions.",
                font=("Segoe UI", 11),
                text_color=("gray25", "gray80"),
                anchor="w",
                justify="left",
                wraplength=400,
            )
            admin_desc_lbl.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 10))

            admin_action_btn = ctk.CTkButton(
                admin_card,
                text="Manage Users",
                command=self.controller.show_user_management,
                height=32,
                font=("Segoe UI", 10, "bold"),
                fg_color=("#3498db", "#2980b9"),  # Blue button for admin
                hover_color=("#2980b9", "#1f5f89"),
            )
            admin_action_btn.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

    def _toggle_profile_dropdown(self) -> None:
        """Toggle profile dropdown menu."""
        if self.profile_dropdown_open:
            self._hide_profile_dropdown()
        else:
            self._show_profile_dropdown()

    def _show_profile_dropdown(self) -> None:
        """Show profile dropdown menu."""
        self.profile_dropdown_open = True

        # Clear existing items
        for widget in self.profile_dropdown.winfo_children():
            widget.destroy()

        # Position dropdown below circular avatar
        # Use profile section position for reliable placement in all modes
        try:
            # Get profile section position (more reliable than individual avatar)
            profile_x = self.profile_section_ref.winfo_rootx() - self.parent.winfo_rootx()
            profile_y = self.profile_section_ref.winfo_rooty() - self.parent.winfo_rooty()
            profile_height = self.profile_section_ref.winfo_height()

            # Position dropdown to the LEFT of profile section, below it
            dropdown_x = profile_x - 420  # 200px wide dropdown positioned to the left
            dropdown_y = profile_y + profile_height + 5

            # Ensure dropdown stays within window bounds
            if dropdown_x < 5:
                dropdown_x = profile_x + self.profile_section_ref.winfo_width()  # Fallback to right side if left is off-screen
            window_width = self.parent.winfo_width()
            if dropdown_x + 200 > window_width:
                dropdown_x = window_width - 205  # Keep margin from right edge

        except Exception as e:
            # Fallback: position to the left of the right edge
            window_width = self.parent.winfo_width() or 1100
            dropdown_x = max(5, window_width - 425)  # Position 200px from right edge, plus margin
            dropdown_y = 80

        self.profile_dropdown.place(x=dropdown_x, y=dropdown_y, anchor="nw")

        # Ensure dropdown is visible and on top of all widgets
        self.profile_dropdown.lift()
        self.profile_dropdown.tkraise()
        self.profile_dropdown.update_idletasks()
        self.parent.update_idletasks()

        # Menu items
        menu_items = [
            ("👤 Profile", lambda: self._navigate_to_profile()),
            ("⚙️ Settings", lambda: self._navigate_to_settings()),
            ("❓ Help", lambda: self._show_help()),
            ("─" * 20, None),
        ]

        for item_text, command in menu_items:
            if item_text.startswith("─"):
                # Separator
                separator = ctk.CTkFrame(
                    self.profile_dropdown,
                    height=1,
                    fg_color=("gray80", "gray30"),
                )
                separator.pack(fill="x", padx=8, pady=4)
            else:
                item_btn = ctk.CTkButton(
                    self.profile_dropdown,
                    text=item_text,
                    command=command if command else None,
                    width=180,
                    height=36,
                    font=("Segoe UI", 11),
                    fg_color="transparent",
                    text_color=("gray20", "gray90"),
                    hover_color=("gray85", "gray30"),
                    anchor="w",
                )
                item_btn.pack(fill="x", padx=8, pady=2)

    def _hide_profile_dropdown(self) -> None:
        """Hide profile dropdown menu."""
        self.profile_dropdown_open = False
        if self.profile_dropdown.winfo_exists():
            self.profile_dropdown.place_forget()

    def _navigate_to_profile(self) -> None:
        """Navigate to profile page."""
        self._hide_profile_dropdown()
        if hasattr(self.controller, "show_profile"):
            self.controller.show_profile()
        else:
            import tkinter.messagebox as mb

            mb.showinfo("Info", "Profile page will be available soon.")

    def _navigate_to_settings(self) -> None:
        """Navigate to settings page."""
        self._hide_profile_dropdown()
        if hasattr(self.controller, "show_settings"):
            self.controller.show_settings()
        else:
            import tkinter.messagebox as mb

            mb.showinfo("Info", "Settings page will be available soon.")

    def _show_help(self) -> None:
        """Show help dialog."""
        self._hide_profile_dropdown()
        import tkinter.messagebox as mb

        mb.showinfo(
            "Help",
            "AutoRBI Help\n\n"
            "• New Work: Upload and process equipment drawings\n"
            "• Report Menu: View and export generated reports\n"
            "• Work History: Browse past work activities\n"
            "• Analytics: View performance metrics\n\n"
            "Keyboard Shortcuts:\n"
            "Ctrl+N - New Work\n"
            "Ctrl+R - Reports\n"
            "Ctrl+H - History\n"
            "Ctrl+A - Analytics",
        )

    def _handle_search(self, query: str) -> None:
        """Handle search input."""
        if not query or len(query) < 2:
            self._hide_search_results()
            return

        # Show search results
        self._show_search_results(query)

    def _show_search_results(self, query: str) -> None:
        """Show search results dropdown."""
        # Clear existing results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

        # Position results below search bar
        self.search_results_frame.place(relx=0.5, y=100, anchor="n", relwidth=0.6)

        # Header
        header_label = ctk.CTkLabel(
            self.search_results_frame,
            text=f"Search results for '{query}'",
            font=("Segoe UI", 11, "bold"),
        )
        header_label.pack(pady=(12, 8), padx=12)

        # TODO: Backend - Get actual search results from backend
        # For now, show placeholder results
        results = [
            ("📄 Report: Equipment Analysis", "Report Menu"),
            ("📊 Work: V-001 Extraction", "Work History"),
            ("🔧 Equipment: E-1002", "Equipment Database"),
        ]

        for result_text, category in results[:5]:  # Limit to 5 results
            result_btn = ctk.CTkButton(
                self.search_results_frame,
                text=f"{result_text} ({category})",
                command=lambda c=category: self._navigate_from_search(c),
                width=300,
                height=32,
                font=("Segoe UI", 10),
                fg_color="transparent",
                text_color=("gray20", "gray90"),
                hover_color=("gray85", "gray30"),
                anchor="w",
            )
            result_btn.pack(fill="x", padx=12, pady=2)

        # No results message if empty
        if not results:
            no_results = ctk.CTkLabel(
                self.search_results_frame,
                text="No results found",
                font=("Segoe UI", 10),
                text_color=("gray50", "gray70"),
            )
            no_results.pack(pady=12)

    def _hide_search_results(self) -> None:
        """Hide search results dropdown."""
        if self.search_results_frame.winfo_exists():
            self.search_results_frame.place_forget()

    def _navigate_from_search(self, category: str) -> None:
        """Navigate to search result category."""
        self._hide_search_results()
        if category == "Report Menu":
            self.controller.show_report_menu()
        elif category == "Work History":
            self.controller.show_work_history()
        # Add more navigation as needed

    def _handle_click_outside(self, event) -> None:
        """Handle clicks outside dropdowns to close them."""
        if not self.profile_dropdown_open:
            return

        # Don't close if clicking on avatar or profile section
        try:
            widget = event.widget
            # Check if click is on avatar frame, avatar label, or profile section
            if hasattr(self, "avatar_frame_ref") and (
                widget == self.avatar_frame_ref
                or str(widget).find("avatar") != -1
                or widget.master == self.avatar_frame_ref
                or widget.master == self.profile_section_ref
            ):
                return
        except:
            pass

        # Check if click is outside profile dropdown
        if self.profile_dropdown.winfo_exists():
            try:
                # Get click coordinates
                x = event.x_root
                y = event.y_root

                # Get dropdown position and size (absolute coordinates)
                dropdown_x = self.profile_dropdown.winfo_rootx()
                dropdown_y = self.profile_dropdown.winfo_rooty()
                dropdown_w = self.profile_dropdown.winfo_width()
                dropdown_h = self.profile_dropdown.winfo_height()

                # Check if click is outside dropdown
                if not (
                    dropdown_x <= x <= dropdown_x + dropdown_w
                    and dropdown_y <= y <= dropdown_y + dropdown_h
                ):
                    self._hide_profile_dropdown()
            except Exception:
                # If any error, just hide the dropdown
                try:
                    self._hide_profile_dropdown()
                except:
                    pass

        # Check if click is outside search results
        if self.search_results_frame and self.search_results_frame.winfo_exists():
            try:
                x, y = event.x_root, event.y_root
                results_x = self.search_results_frame.winfo_x()
                results_y = self.search_results_frame.winfo_y()
                results_w = self.search_results_frame.winfo_width()
                results_h = self.search_results_frame.winfo_height()

                if not (
                    results_x <= x <= results_x + results_w
                    and results_y <= y <= results_y + results_h
                ):
                    self._hide_search_results()
            except:
                pass

    def _create_kpi_card(self, parent: ctk.CTkFrame, title: str, value: str, key: str, row: int, col: int) -> None:
        """Create a KPI metric card."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 11),
            text_color=("gray50", "gray70"),
        )
        title_label.pack(pady=(12, 4))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 20, "bold"),
        )
        value_label.pack(pady=(0, 12))

        self.kpi_cards[key] = card

    def _change_period(self, period: str) -> None:
        """Change analytics time period (button-based, no input fields)."""
        # TODO: Backend - Query analytics for selected time period
        # TODO: Backend - Calculate metrics for the period (daily, weekly, monthly, all-time)
        # TODO: Backend - Return updated KPI values
        self.current_period = period
        # self.controller.load_analytics(period)
