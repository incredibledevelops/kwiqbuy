from pydantic import BaseModel, Field


class OTPRequestIn(BaseModel):
    phone: str = Field(min_length=9, max_length=20)
    full_name: str = Field(min_length=2, max_length=100)


class OTPRequestOut(BaseModel):
    message: str
    expires_in_minutes: int


class OTPVerifyIn(BaseModel):
    phone: str
    code: str = Field(min_length=4, max_length=8)


class OTPVerifyOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_customer: bool
    customer_id: str
    full_name: str


class RefreshRequest(BaseModel):
    refresh_token: str