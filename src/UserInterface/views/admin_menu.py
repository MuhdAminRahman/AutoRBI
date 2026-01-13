"""Admin menu view for AutoRBI application (CustomTkinter)."""

import os
from datetime import datetime
from typing import Dict, List, Optional

from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil

from UserInterface.services.database_service import DatabaseService
from AutoRBI_Database.database.session import SessionLocal

class AdminMenuView:
    """Handles the admin menu interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._logo_image: Optional[ctk.CTkImage] = self._load_logo()
        self._datetime_label: Optional[ctk.CTkLabel] = None
        self.profile_dropdown_open = False
        self.search_results_frame: Optional[ctk.CTkFrame] = None
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

        # Logout button (red color)
        logout_btn = ctk.CTkButton(
            profile_section,
            text="Logout",
            command=self.controller.logout,
            width=100,
            height=36,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#e74c3c", "#c0392b"),
            hover_color=("#c0392b", "#a93226"),
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

        # Main content area - Scrollable
        main_frame = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        main_frame.grid_columnconfigure(0, weight=1)

        # ========== ADMIN HEADER WITH BADGE ==========
        header_section = ctk.CTkFrame(
            main_frame,
            fg_color=("gray95", "gray18"),
            corner_radius=12,
            border_width=2,
            border_color=("#e74c3c", "#c0392b"),  # Red admin border
        )
        header_section.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 18))
        header_section.grid_columnconfigure(0, weight=1)

        # Admin badge and title
        title_container = ctk.CTkFrame(header_section, fg_color="transparent")
        title_container.grid(row=0, column=0, sticky="w", padx=20, pady=16)

        # Admin badge
        admin_badge = ctk.CTkFrame(
            title_container,
            fg_color=("#e74c3c", "#c0392b"),
            corner_radius=6,
        )
        admin_badge.pack(side="left", padx=(0, 12))

        badge_label = ctk.CTkLabel(
            admin_badge,
            text="⚡ ADMIN",
            font=("Segoe UI", 10, "bold"),
            text_color="white",
        )
        badge_label.pack(padx=10, pady=4)

        # Section title
        welcome_label = ctk.CTkLabel(
            title_container,
            text="Control Panel",
            font=("Segoe UI", 26, "bold"),
        )
        welcome_label.pack(side="left")

        subtitle_label = ctk.CTkLabel(
            header_section,
            text="System-wide oversight • User management • Performance analytics",
            font=("Segoe UI", 11),
            text_color=("gray40", "gray75"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        # ========== ANALYTICS DASHBOARD SECTION ==========
        self._build_embedded_analytics(main_frame, row=2)

        # ========== RECENT ACTIVITY FEED ==========
        self._build_recent_activity_feed(main_frame, row=3)

        # ========== ADMINISTRATIVE TOOLS SECTION ==========
        actions_title = ctk.CTkLabel(
            main_frame,
            text="🛠️ Administrative Tools",
            font=("Segoe UI", 18, "bold"),
        )
        actions_title.grid(row=5, column=0, sticky="w", padx=24, pady=(24, 12))

        # Menu buttons container (2x2 grid)
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, sticky="ew", padx=24, pady=(0, 24))

        # Configure grid for 2 columns
        buttons_frame.grid_columnconfigure(0, weight=1, uniform="menu_col")
        buttons_frame.grid_columnconfigure(1, weight=1, uniform="menu_col")

        # Admin tool configurations with icons and colors
        admin_tools = [
            {
                "icon": "👥",
                "title": "User Management",
                "description": "Manage user accounts, roles, and access permissions.",
                "command": self.controller.show_user_management,
                "color": ("#3498db", "#2980b9"),  # Blue
            },
            {
                "icon": "📋",
                "title": "Work Assignment",
                "description": "Create works and assign engineers to projects.",
                "command": self.controller.show_work_management,
                "color": ("#9b59b6", "#8e44ad"),  # Purple
            },
            {
                "icon": "📊",
                "title": "User Analytics",
                "description": "View team performance, productivity insights, and user activity metrics.",
                "command": self.controller.show_admin_analytics,
                "color": ("#2ecc71", "#27ae60"),  # Green
            },
            {
                "icon": "📄",
                "title": "Report Menu",
                "description": "Generate and review system-wide reports and documentation.",
                "command": self.controller.show_report_menu,
                "color": ("#f39c12", "#e67e22"),  # Orange
            },
        ]

        # Create cards in 2x2 grid
        for idx, tool in enumerate(admin_tools):
            row = idx // 2
            col = idx % 2

            # Card with hover effect
            card = ctk.CTkFrame(
                buttons_frame,
                corner_radius=14,
                border_width=2,
                border_color=("gray85", "gray28"),
                fg_color=("white", "gray17"),
            )
            card.grid(
                row=row,
                column=col,
                padx=10,
                pady=10,
                sticky="nsew",
            )

            # Add hover effects
            def on_enter(e, c=card, color=tool["color"]):
                c.configure(
                    border_color=color,
                    fg_color=("gray98", "gray19"),
                )

            def on_leave(e, c=card):
                c.configure(
                    border_color=("gray85", "gray28"),
                    fg_color=("white", "gray17"),
                )

            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            card.grid_columnconfigure(0, weight=1)

            # Icon badge at top
            icon_frame = ctk.CTkFrame(
                card,
                width=56,
                height=56,
                corner_radius=28,
                fg_color=tool["color"],
            )
            icon_frame.grid(row=0, column=0, pady=(20, 12))
            icon_frame.grid_propagate(False)

            icon_label = ctk.CTkLabel(
                icon_frame,
                text=tool["icon"],
                font=("Segoe UI", 26),
            )
            icon_label.place(relx=0.5, rely=0.5, anchor="center")

            # Title
            title_lbl = ctk.CTkLabel(
                card,
                text=tool["title"],
                font=("Segoe UI", 16, "bold"),
            )
            title_lbl.grid(row=1, column=0, padx=20, pady=(0, 8))

            # Description
            desc_lbl = ctk.CTkLabel(
                card,
                text=tool["description"],
                font=("Segoe UI", 10),
                text_color=("gray40", "gray75"),
                wraplength=220,
                justify="center",
            )
            desc_lbl.grid(row=2, column=0, padx=20, pady=(0, 16))

            # Action button
            action_btn = ctk.CTkButton(
                card,
                text="Open",
                command=tool["command"],
                height=36,
                font=("Segoe UI", 11, "bold"),
                fg_color=tool["color"],
                hover_color=tool["color"][1],
                corner_radius=8,
            )
            action_btn.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

    def initialize_analytics_data(self) -> Dict[str, int]:
        """Get system-wide analytics for admin dashboard (ALL users' data)."""
        try:
            db = SessionLocal()
            # Get SYSTEM-WIDE data (no user_id filter for admins)
            completed_work = DatabaseService.get_system_work_completion_percentage(
                db=db
            )
            
            total_equipment = DatabaseService.get_system_total_equipment_count(
                db=db
            )
            
            extracted_equipment = DatabaseService.get_system_extracted_equipment_count(
                db=db
            )
            
            # Calculate average health score across ALL works
            """
            health score is based on these factors:

            Equipment completion (fields filled)

            Component completion (fields filled)

            Data extraction status (has extracted_date)

            Data quality (values are valid/complete)
            """
            avg_health_score = DatabaseService.get_system_average_health_score(
                db=db
            )
            
            # Calculate completion rate
            total_percentage = 0
            for work in completed_work.values():
                total_percentage += work
            completion_rate = int(total_percentage / len(completed_work)) if completed_work else 0
            
            analytics_data = {
                "work_completion": completion_rate if completion_rate is not None else 0,
                "total_equipment": total_equipment if total_equipment is not None else 0,
                "equipment_extracted": extracted_equipment if extracted_equipment is not None else 0,
                "avg_health_score": int(avg_health_score) if avg_health_score is not None else 0,
            }
            return analytics_data
        except Exception as e:
            # Log error and return zeros on failure
            print(f"Error initializing admin analytics data: {e}")
            return {
                "work_completion": 0,
                "total_equipment": 0,
                "equipment_extracted": 0,
                "avg_health_score": 0,
            }
        finally:
            db.close()
        

    def _build_embedded_analytics(self, parent, row: int):
        """Embedded analytics overview in main menu with simplified metrics."""
        # Analytics container with distinct admin styling
        analytics_section = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=2,
            border_color=("#3498db", "#2980b9"),  # Blue admin border
            fg_color=("white", "gray17"),
        )
        analytics_section.grid(row=row, column=0, sticky="ew", padx=24, pady=(0, 18))
        analytics_section.grid_columnconfigure(0, weight=1)

        # Analytics header with badge
        header_frame = ctk.CTkFrame(analytics_section, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 14))
        header_frame.grid_columnconfigure(0, weight=1)

        # Header container for badge + title
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, sticky="w")

        # System-wide badge
        system_badge = ctk.CTkFrame(
            title_container,
            fg_color=("#3498db", "#2980b9"),
            corner_radius=6,
        )
        system_badge.pack(side="left", padx=(0, 10))

        badge_text = ctk.CTkLabel(
            system_badge,
            text="SYSTEM-WIDE",
            font=("Segoe UI", 9, "bold"),
            text_color="white",
        )
        badge_text.pack(padx=8, pady=3)

        analytics_title = ctk.CTkLabel(
            title_container,
            text="📊 Analytics Overview",
            font=("Segoe UI", 18, "bold"),
        )
        analytics_title.pack(side="left")

        analytics_subtitle = ctk.CTkLabel(
            header_frame,
            text="Real-time system metrics across all users and projects",
            font=("Segoe UI", 10),
            text_color=("gray40", "gray75"),
        )
        analytics_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # ========== BACKEND INTEGRATION ==========
        analytics_data = self.initialize_analytics_data()
        
        # Placeholder data for demonstration (REMOVE WHEN BACKEND IS IMPLEMENTED)
        work_completion = analytics_data["work_completion"]  # % of work completed/total work
        equipment_extracted = analytics_data["equipment_extracted"]  # number extracted
        total_equipment = analytics_data["total_equipment"]  # total equipment
        avg_health_score = analytics_data["avg_health_score"]  # average health score

        # Metrics container with 3 circular progress indicators
        metrics_container = ctk.CTkFrame(
            analytics_section,
            fg_color="transparent",
        )
        metrics_container.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        metrics_container.grid_columnconfigure(0, weight=1, uniform="metric")
        metrics_container.grid_columnconfigure(1, weight=1, uniform="metric")
        metrics_container.grid_columnconfigure(2, weight=1, uniform="metric")

        # Metric 1: Work Completion
        self._create_circular_metric(
            metrics_container,
            column=0,
            icon="📋",
            title="Work Completion",
            value=f"{work_completion}%",
            subtitle=f"{work_completion} of 100 tasks",
            color=("#3498db", "#2980b9"),
        )

        # Metric 2: Equipment Extracted
        extraction_percent = (
            int((equipment_extracted / total_equipment) * 100)
            if total_equipment > 0
            else 0
        )
        self._create_circular_metric(
            metrics_container,
            column=1,
            icon="🔧",
            title="Equipment Extracted",
            value=f"{equipment_extracted}/{total_equipment}",
            subtitle=f"{extraction_percent}% complete",
            color=("#9b59b6", "#8e44ad"),
        )

        # Metric 3: Average Health Score
        health_color = self._get_health_color(avg_health_score)
        self._create_circular_metric(
            metrics_container,
            column=2,
            icon=(
                "💚"
                if avg_health_score >= 80
                else "💛" if avg_health_score >= 60 else "❤️"
            ),
            title="Avg Health Score",
            value=f"{avg_health_score}/100",
            subtitle=self._get_health_status(avg_health_score),
            color=health_color,
        )

        # Analytics buttons at bottom
        buttons_container = ctk.CTkFrame(analytics_section, fg_color="transparent")
        buttons_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 18))

        view_analytics_btn = ctk.CTkButton(
            buttons_container,
            text="📊 Work Analytics",
            command=self.controller.show_analytics,
            width=160,
            height=38,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#21618c"),
            corner_radius=8,
        )
        view_analytics_btn.pack(side="left", padx=(0, 10))

        # Add User Analytics button
        user_analytics_btn = ctk.CTkButton(
            buttons_container,
            text="👥 User Analytics",
            command=self.controller.show_admin_analytics,
            width=160,
            height=38,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
            corner_radius=8,
        )
        user_analytics_btn.pack(side="left")

    def _build_recent_activity_feed(self, parent, row: int):
        """Build Recent Activity Feed section showing latest system activities."""
        # Section title
        activity_title = ctk.CTkLabel(
            parent,
            text="🕒 Recent Activity",
            font=("Segoe UI", 18, "bold"),
        )
        activity_title.grid(row=row, column=0, sticky="w", padx=24, pady=(18, 12))

        # Activity container with border
        activity_section = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=2,
            border_color=("#9b59b6", "#8e44ad"),  # Purple border
            fg_color=("white", "gray17"),
        )
        activity_section.grid(row=row + 1, column=0, sticky="ew", padx=24, pady=(0, 18))

        # Get recent activities from database
        activities = self._get_recent_activities()

        if not activities:
            # No activities placeholder
            no_activity = ctk.CTkLabel(
                activity_section,
                text="No recent activity to display",
                font=("Segoe UI", 11),
                text_color=("gray60", "gray80"),
            )
            no_activity.pack(pady=40)
            return

        # Activity feed container (scrollable if needed)
        activity_feed = ctk.CTkFrame(activity_section, fg_color="transparent")
        activity_feed.pack(fill="both", expand=True, padx=20, pady=18)

        # Display activities in timeline format
        for idx, activity in enumerate(activities[:8]):  # Show max 8 activities
            self._create_activity_item(activity_feed, activity, idx)

        # "View All" button at bottom
        view_all_btn = ctk.CTkButton(
            activity_section,
            text="View Full History →",
            command=self.controller.show_work_history,
            width=140,
            height=32,
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            text_color=("#9b59b6", "#8e44ad"),
            hover_color=("gray90", "gray25"),
            border_width=2,
            border_color=("#9b59b6", "#8e44ad"),
            corner_radius=8,
        )
        view_all_btn.pack(pady=(0, 18))

    def _create_activity_item(self, parent, activity: dict, index: int):
        """Create a single activity item in timeline format."""
        # Activity row
        activity_row = ctk.CTkFrame(
            parent,
            fg_color=("gray95", "gray20"),
            corner_radius=10,
        )
        activity_row.pack(fill="x", pady=(0, 8))
        activity_row.grid_columnconfigure(1, weight=1)

        # Icon/color based on action type
        action_icons = {
            "upload_pdf": ("📤", "#3498db"),
            "extract": ("🔍", "#2ecc71"),
            "correct": ("✏️", "#f39c12"),
            "generate_excel": ("📊", "#9b59b6"),
            "generate_ppt": ("📑", "#e74c3c"),
            "login": ("🔓", "#16a085"),
            "work_created": ("➕", "#9b59b6"),
            "work_assigned": ("👥", "#3498db"),
        }

        icon, color = action_icons.get(
            activity.get("action_type", ""),
            ("📋", "#95a5a6")  # Default
        )

        # Icon badge
        icon_frame = ctk.CTkFrame(
            activity_row,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=color,
        )
        icon_frame.grid(row=0, column=0, padx=12, pady=10)
        icon_frame.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=("Segoe UI", 16),
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Activity details
        details_frame = ctk.CTkFrame(activity_row, fg_color="transparent")
        details_frame.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        # Main text
        main_text = ctk.CTkLabel(
            details_frame,
            text=activity.get("description", "Activity"),
            font=("Segoe UI", 11),
            anchor="w",
        )
        main_text.pack(anchor="w")

        # Metadata (user + time)
        metadata_text = f"{activity.get('user', 'Unknown')} • {activity.get('time_ago', 'Unknown')}"
        metadata_label = ctk.CTkLabel(
            details_frame,
            text=metadata_text,
            font=("Segoe UI", 9),
            text_color=("gray50", "gray70"),
            anchor="w",
        )
        metadata_label.pack(anchor="w", pady=(2, 0))

    def _get_recent_activities(self) -> List[Dict]:
        """
        Fetch recent activities from work history.

        Returns list of activity dicts with:
        - action_type: str
        - description: str
        - user: str (username or full name)
        - time_ago: str (human-readable time)
        - timestamp: datetime
        """
        try:
            db = SessionLocal()
            from AutoRBI_Database.database.models.work_history import WorkHistory
            from AutoRBI_Database.database.models.users import User
            from datetime import datetime, timezone

            # Get last 10 activities with user info
            results = (
                db.query(WorkHistory, User)
                .join(User, WorkHistory.user_id == User.user_id)
                .order_by(WorkHistory.timestamp.desc())
                .limit(10)
                .all()
            )

            activities = []
            for history, user in results:
                # Calculate time ago
                time_ago = self._format_time_ago(history.timestamp)

                # Format description
                description = history.description or f"{history.action_type.replace('_', ' ').title()}"

                activities.append({
                    "action_type": history.action_type,
                    "description": description,
                    "user": user.full_name or user.username,
                    "time_ago": time_ago,
                    "timestamp": history.timestamp,
                })

            return activities

        except Exception as e:
            print(f"Error fetching recent activities: {e}")
            return []
        finally:
            db.close()

    def _format_time_ago(self, timestamp) -> str:
        """Format timestamp as human-readable 'time ago' string."""
        if not timestamp:
            return "Unknown"

        try:
            from datetime import datetime, timezone

            # Ensure timestamp is timezone-aware
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            delta = now - timestamp

            seconds = delta.total_seconds()

            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes}m ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours}h ago"
            elif seconds < 604800:
                days = int(seconds / 86400)
                return f"{days}d ago"
            else:
                return timestamp.strftime("%b %d")
        except Exception:
            return "Unknown"

    def _create_circular_metric(
        self,
        parent,
        column: int,
        icon: str,
        title: str,
        value: str,
        subtitle: str,
        color: tuple,
    ):
        """Create a circular metric card with icon and values."""
        # TODO: Backend - Future Enhancement: Implement circular progress ring visualization
        # TODO: Backend - Add animated progress ring around the icon
        # TODO: Backend - Progress ring should fill based on percentage value
        # TODO: Backend - Use libraries like matplotlib or custom canvas drawing for progress ring

        metric_card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=("gray95", "gray18"),
            border_width=1,
            border_color=("gray85", "gray25"),
        )
        metric_card.grid(row=0, column=column, padx=8, pady=8, sticky="nsew")
        metric_card.grid_columnconfigure(0, weight=1)

        # Icon with circular background
        icon_frame = ctk.CTkFrame(
            metric_card,
            width=60,
            height=60,
            corner_radius=30,
            fg_color=color,
        )
        icon_frame.grid(row=0, column=0, pady=(16, 8))
        icon_frame.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=("Segoe UI", 28),
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title_label = ctk.CTkLabel(
            metric_card,
            text=title,
            font=("Segoe UI", 11, "bold"),
            text_color=("gray30", "gray90"),
        )
        title_label.grid(row=1, column=0, pady=(0, 4))

        # Main value
        value_label = ctk.CTkLabel(
            metric_card,
            text=value,
            font=("Segoe UI", 20, "bold"),
            text_color=color,
        )
        value_label.grid(row=2, column=0, pady=(0, 4))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            metric_card,
            text=subtitle,
            font=("Segoe UI", 9),
            text_color=("gray50", "gray70"),
        )
        subtitle_label.grid(row=3, column=0, pady=(0, 16))

    def _get_health_color(self, score: int) -> tuple:
        """Get color based on health score."""
        # TODO: Backend - Ensure this logic matches RBIAnalyticsEngine.get_work_health_score()
        # TODO: Backend - Current thresholds: >=80 (Green), >=60 (Orange), <60 (Red)
        # TODO: Backend - Align with RBIAnalyticsEngine thresholds if different
        if score >= 80:
            return ("#2ecc71", "#27ae60")  # Green
        elif score >= 60:
            return ("#f39c12", "#e67e22")  # Orange
        else:
            return ("#e74c3c", "#c0392b")  # Red

    def _get_health_status(self, score: int) -> str:
        """Get health status text based on score."""
        # TODO: Backend - Ensure this logic matches RBIAnalyticsEngine risk level mapping
        # TODO: Backend - Consider using same status strings as analytics.py (LOW-Ready, MEDIUM-Review, HIGH-Gaps, CRITICAL)
        # TODO: Backend - Current implementation uses simplified status for overview
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        else:
            return "Needs Attention"

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
        # Calculate position: right side of window, below header
        window_width = self.parent.winfo_width() or 1100  # Default if not yet rendered
        dropdown_x = window_width - 220  # 200px from right + 20px padding
        self.profile_dropdown.place(x=dropdown_x, y=80, anchor="ne")

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