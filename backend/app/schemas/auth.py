from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = None
    role: UserRole = UserRole.STAFF
    vendor_id: Optional[str] = None
    vehicle: Optional[str] = None
    plate_number: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    vendor_id: Optional[str] = None
    vehicle: Optional[str] = None
    plate_number: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ProfileUpdateIn(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    vendor_id: Optional[str] = None
    vehicle: Optional[str] = None
    plate_number: Optional[str] = None
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "6512a3b4c5d6e7f8a9b0c1d2",
                    "full_name": "Ali Mensah",
                    "email": "ali@kwiqbuy.com",
                    "phone": "0534634845",
                    "role": "vendor",
                    "is_active": True,
                    "vendor_id": "6512a3b4c5d6e7f8a9b0c1d3",
                    "created_at": "2026-01-15T10:30:00+00:00",
                }
            ]
        },
    }
