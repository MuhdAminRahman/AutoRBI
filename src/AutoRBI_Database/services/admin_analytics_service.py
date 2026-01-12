"""
Admin Analytics Service
Business logic for admin-only user performance analytics and team metrics.
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from AutoRBI_Database.logging_config import get_logger
from AutoRBI_Database.database.crud.user_analytics_crud import (
    get_user_activity_summary,
    get_team_performance_comparison,
    get_work_duration_by_user,
    get_hourly_productivity,
    get_daily_activity,
)
from AutoRBI_Database.exceptions import (
    ValidationError,
    DatabaseError,
    UnauthorizedAccessError,
)

logger = get_logger(__name__)


def check_admin_permission(current_user: dict) -> None:
    """
    Verify that the current user has admin privileges.

    Args:
        current_user: Current user session data

    Raises:
        UnauthorizedAccessError: If user is not an admin
    """
    if current_user.get("role") != "Admin":
        raise UnauthorizedAccessError(
            "Analytics features are only available to administrators"
        )


def get_user_performance_summary(
    db: Session,
    current_user: dict,
    user_id: int,
    period: str = "last_7_days"
) -> Dict:
    """
    Get comprehensive performance summary for a specific user.

    Args:
        db: Database session
        current_user: Current user session data
        user_id: ID of user to analyze
        period: Time period ("today", "last_7_days", "last_month", "all")

    Returns:
        {
            "success": bool,
            "data": dict with user performance metrics,
            "message": str (optional error message)
        }
    """
    try:
        # Permission check
        check_admin_permission(current_user)

        logger.info(
            f"Admin {current_user.get('username')} requesting performance summary "
            f"for user {user_id} (period: {period})"
        )

        # Calculate date range
        start_date, end_date = _calculate_date_range(period)

        # Get user summary from CRUD
        summary = get_user_activity_summary(db, user_id, start_date, end_date)

        # Get additional context - user info
        from AutoRBI_Database.database.crud.user_crud import get_user_by_id
        user = get_user_by_id(db, user_id)

        if not user:
            return {
                "success": False,
                "message": f"User with ID {user_id} not found"
            }

        # Enrich summary with user details
        summary["username"] = user.username
        summary["full_name"] = user.full_name
        summary["email"] = user.email
        summary["role"] = user.role

        logger.info(f"Successfully retrieved performance summary for user {user_id}")

        return {
            "success": True,
            "data": summary
        }

    except UnauthorizedAccessError as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "unauthorized"
        }
    except Exception as e:
        logger.error(f"Error retrieving user performance summary: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve performance summary. Please try again.",
            "error_type": "system_error"
        }


def get_team_comparison(
    db: Session,
    current_user: dict,
    period: str = "last_7_days"
) -> Dict:
    """
    Get team-wide performance comparison across all engineers.

    Args:
        db: Database session
        current_user: Current user session data
        period: Time period filter

    Returns:
        {
            "success": bool,
            "data": List of user performance dictionaries,
            "summary": Overall team statistics
        }
    """
    try:
        # Permission check
        check_admin_permission(current_user)

        logger.info(
            f"Admin {current_user.get('username')} requesting team comparison "
            f"(period: {period})"
        )

        # Calculate date range
        start_date, end_date = _calculate_date_range(period)

        # Get team comparison data
        team_data = get_team_performance_comparison(db, start_date, end_date)

        # Calculate team summary statistics
        total_engineers = len(team_data)
        total_actions = sum(user["total_actions"] for user in team_data)
        total_equipment = sum(user["equipment_extracted"] for user in team_data)
        avg_time = (
            sum(user["avg_time_per_equipment_minutes"] for user in team_data if user["avg_time_per_equipment_minutes"] > 0) /
            len([u for u in team_data if u["avg_time_per_equipment_minutes"] > 0])
            if any(u["avg_time_per_equipment_minutes"] > 0 for u in team_data)
            else 0
        )

        summary = {
            "total_engineers": total_engineers,
            "total_team_actions": total_actions,
            "total_equipment_extracted": total_equipment,
            "team_avg_time_per_equipment": round(avg_time, 2),
            "period": period
        }

        logger.info(f"Successfully retrieved team comparison data ({total_engineers} engineers)")

        return {
            "success": True,
            "data": team_data,
            "summary": summary
        }

    except UnauthorizedAccessError as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "unauthorized"
        }
    except Exception as e:
        logger.error(f"Error retrieving team comparison: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve team comparison. Please try again.",
            "error_type": "system_error"
        }


def get_work_timeline(
    db: Session,
    current_user: dict,
    work_id: int
) -> Dict:
    """
    Get timeline of user activities on a specific work.

    Args:
        db: Database session
        current_user: Current user session data
        work_id: ID of work to analyze

    Returns:
        {
            "success": bool,
            "data": List of user timelines,
            "work_info": Work details
        }
    """
    try:
        # Permission check
        check_admin_permission(current_user)

        logger.info(
            f"Admin {current_user.get('username')} requesting work timeline "
            f"for work {work_id}"
        )

        # Get work duration data
        timeline_data = get_work_duration_by_user(db, work_id)

        # Get work info
        from AutoRBI_Database.database.crud.work_crud import get_work_by_id
        work = get_work_by_id(db, work_id)

        if not work:
            return {
                "success": False,
                "message": f"Work with ID {work_id} not found"
            }

        work_info = {
            "work_id": work.work_id,
            "work_name": work.work_name,
            "status": work.status,
            "created_at": work.created_at.isoformat() if work.created_at else None
        }

        logger.info(f"Successfully retrieved work timeline for work {work_id}")

        return {
            "success": True,
            "data": timeline_data,
            "work_info": work_info
        }

    except UnauthorizedAccessError as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "unauthorized"
        }
    except Exception as e:
        logger.error(f"Error retrieving work timeline: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve work timeline. Please try again.",
            "error_type": "system_error"
        }


def get_productivity_insights(
    db: Session,
    current_user: dict,
    user_id: Optional[int] = None,
    period: str = "last_7_days"
) -> Dict:
    """
    Get productivity insights including hourly patterns and daily activity.

    Args:
        db: Database session
        current_user: Current user session data
        user_id: Optional user ID (None = all users)
        period: Time period filter

    Returns:
        {
            "success": bool,
            "data": {
                "hourly_productivity": List,
                "daily_activity": List,
                "peak_hours": Dict,
                "insights": Dict
            }
        }
    """
    try:
        # Permission check
        check_admin_permission(current_user)

        logger.info(
            f"Admin {current_user.get('username')} requesting productivity insights "
            f"(user_id: {user_id}, period: {period})"
        )

        # Calculate date range
        start_date, end_date = _calculate_date_range(period)

        # Get hourly productivity data
        hourly_data = get_hourly_productivity(db, user_id, start_date, end_date)

        # Get daily activity data
        daily_data = get_daily_activity(db, user_id, start_date, end_date)

        # Calculate peak hours
        peak_hours = {}
        if hourly_data:
            max_hour = max(hourly_data, key=lambda x: x["action_count"])
            min_hour = min(hourly_data, key=lambda x: x["action_count"])

            peak_hours = {
                "most_productive_hour": max_hour["hour"],
                "most_productive_count": max_hour["action_count"],
                "least_productive_hour": min_hour["hour"],
                "least_productive_count": min_hour["action_count"]
            }

        # Generate insights
        insights = {
            "total_days_active": len(daily_data),
            "avg_actions_per_day": (
                round(sum(d["action_count"] for d in daily_data) / len(daily_data), 2)
                if daily_data else 0
            ),
            "most_active_day": (
                max(daily_data, key=lambda x: x["action_count"])["date"]
                if daily_data else None
            )
        }

        logger.info("Successfully retrieved productivity insights")

        return {
            "success": True,
            "data": {
                "hourly_productivity": hourly_data,
                "daily_activity": daily_data,
                "peak_hours": peak_hours,
                "insights": insights
            }
        }

    except UnauthorizedAccessError as e:
        logger.warning(f"Unauthorized access attempt: {e}")
        return {
            "success": False,
            "message": str(e),
            "error_type": "unauthorized"
        }
    except Exception as e:
        logger.error(f"Error retrieving productivity insights: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to retrieve productivity insights. Please try again.",
            "error_type": "system_error"
        }


def _calculate_date_range(period: str) -> tuple:
    """
    Convert period string to date range (start_date, end_date).

    Args:
        period: One of "all", "today", "last_7_days", "last_month"

    Returns:
        Tuple of (start_date, end_date) as datetime objects
    """
    now = datetime.utcnow()

    if period == "all":
        return None, None
    elif period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end
    elif period == "last_7_days":
        start = now - timedelta(days=7)
        return start, now
    elif period == "last_month":
        start = now - timedelta(days=30)
        return start, now
    else:
        logger.warning(f"Unknown period filter: {period}, defaulting to 'all'")
        return None, None
