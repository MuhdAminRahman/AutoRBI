from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Utility to hash passwords
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Utility to verify passwords
def verify_password(plain_pw: str, hashed_pw: str) -> bool:
    return pwd_context.verify(plain_pw, hashed_pw)

# Normalizers for User fields
def normalize_user_status(value):
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ["active", "a", "enabled", "yes", "true", "1"]:
        return "Active"
    if v in ["inactive", "i", "disabled", "no", "false", "0"]:
        return "Inactive"
    return None



# 1. Create user (Admin OR Engineer)
def create_user(db: Session, username: str, full_name: str, password: str, role: str = "Engineer"):
    hashed_pw = hash_password(password)

    user = User(
        username=username,
        full_name=full_name,
        password=hashed_pw,
        role=role,
        status="Active"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# 2. Engineer self-registration (role fixed to Engineer)
def register_engineer(db: Session, username: str, full_name: str, password: str):
    return create_user(db, username, full_name, password, role="Engineer")


# 3. Get user by ID
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()


# 4. Get user by username (used for login)
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


# 5. Get all users (Admin)
def get_all_users(db: Session):
    return db.query(User).all()


# 6. Get all active users
def get_active_users(db: Session):
    return db.query(User).filter(User.status == "Active").all()


# 7. Admin updates a user
def admin_update_user(db: Session, user_id: int, updates: dict):
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    if "full_name" in updates:
        user.full_name = updates["full_name"]

    if "username" in updates:
        user.username = updates["username"]

    if "role" in updates:
        user.role = updates["role"]

    if "status" in updates:
        normalized = normalize_user_status(updates["status"])
        if normalized is None:
            raise ValueError(f"Invalid user status: {updates['status']}")
        user.status = normalized


    if "password" in updates:
        user.password = hash_password(updates["password"])

    db.commit()
    return user


# 8. Engineer updates their own profile
def engineer_update_self(db: Session, user_id: int, full_name=None, password=None):
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    if full_name:
        user.full_name = full_name

    if password:
        user.password = hash_password(password)

    db.commit()
    return user


# 9. Soft delete user
def deactivate_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.status = "Inactive"
    db.commit()
    return user


# 10. Login function (validates credentials)
def login_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)

    if not user:
        return None, "User not found"

    if user.status != "Active":
        return None, "Account inactive"

    if not verify_password(password, user.password):
        return None, "Invalid password"

    return user, "Login successful"
