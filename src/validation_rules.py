"""Placeholder validation rules for UI until backend integration is complete."""

class UsernameRules:
    """Username validation rules."""
    MIN_LENGTH = 3
    MAX_LENGTH = 50
    ALLOWED_CHARS = "letters, numbers, underscore, hyphen"

class PasswordRules:
    """Password validation rules."""
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = False

def get_username_validation_error(username: str) -> str | None:
    """Validate username and return error message or None if valid."""
    if not username:
        return "Username is required"

    if len(username) < UsernameRules.MIN_LENGTH:
        return f"Username must be at least {UsernameRules.MIN_LENGTH} characters"

    if len(username) > UsernameRules.MAX_LENGTH:
        return f"Username must be at most {UsernameRules.MAX_LENGTH} characters"

    # Check for valid characters (letters, numbers, underscore, hyphen)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return "Username can only contain letters, numbers, underscore, and hyphen"

    return None

def get_password_validation_error(password: str) -> str | None:
    """Validate password and return error message or None if valid."""
    if not password:
        return "Password is required"

    if len(password) < PasswordRules.MIN_LENGTH:
        return f"Password must be at least {PasswordRules.MIN_LENGTH} characters"

    if len(password) > PasswordRules.MAX_LENGTH:
        return f"Password must be at most {PasswordRules.MAX_LENGTH} characters"

    if PasswordRules.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter"

    if PasswordRules.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter"

    if PasswordRules.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        return "Password must contain at least one digit"

    return None