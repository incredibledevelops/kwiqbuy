from typing import List, Optional

from pydantic import BaseModel, Field


class TwoFASetupOut(BaseModel):
    secret: str
    provisioning_uri: str
    qr_data_url: str


class TwoFAVerifyIn(BaseModel):
    code: str = Field(min_length=6, max_length=10)


class TwoFAVerifyOut(BaseModel):
    enabled: bool
    message: str
    recovery_codes: List[str] = []


class TwoFADisableIn(BaseModel):
    password: str
    code: Optional[str] = None


class TwoFAStatusOut(BaseModel):
    enabled: bool
    verified_at: Optional[str] = None
    recovery_codes_remaining: int = 0


class LoginTwoFARequired(BaseModel):
    needs_2fa: bool = True
    temp_token: str
    message: str = "2FA code required"


class TwoFALoginIn(BaseModel):
    temp_token: str
    code: str
