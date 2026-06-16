import enum

class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"