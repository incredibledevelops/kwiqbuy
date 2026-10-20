import os
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import (
    create_customer_access_token,
    create_customer_refresh_token,
)
from app.crud import customer as customer_crud
from app.crud import otp as otp_crud
from app.models.otp import OTPPurpose

router = APIRouter()

class OTPRequest(BaseModel):
    phone: str
    full_name: str | None = None

class OTPVerify(BaseModel):
    phone: str
    code: str

@router.post("/request-otp")
@limiter.limit(settings.RATE_LIMIT_OTP)
async def request_otp(request: Request, payload: OTPRequest):
    # 1. Generate and save OTP to database
    otp = await otp_crud.create_otp(phone=payload.phone, purpose=OTPPurpose.LOGIN)
    
    # 2. Check Environment
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment != "production":
        # --- DEV MODE ---
        print(f"📱 [DEV MODE] OTP for {payload.phone} is: {otp.code}")
        return {
            "status": "success",
            "message": "DEV MODE: SMS bypassed.",
            "is_dev_mode": True,
            "dev_otp": otp.code,
            "expires_in": 300
        }
        
    else:
        # --- PRODUCTION MODE ---
        from app.core.sms import send_sms
        message = f"Your KwiqBuy verification code is {otp.code}. Valid for 5 minutes."
        sent = await send_sms(payload.phone, message)
        
        if not sent:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send SMS. Please try again later."
            )

        return {
            "status": "success",
            "message": "Code sent via SMS.",
            "is_dev_mode": False
        }


@router.post("/verify-otp")
async def verify_otp(payload: OTPVerify):
    # 1. Verify the code against the database
    is_valid, error_msg = await otp_crud.verify_otp(
        phone=payload.phone,
        code=payload.code,
        purpose=OTPPurpose.LOGIN
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # 2. Get or create the customer
    # We default the name to "Customer" if they are brand new
    customer = await customer_crud.get_or_create(
        phone=payload.phone,
        full_name="Customer",
    )

    # 3. Generate tokens
    access_token = create_customer_access_token(
        phone=customer.phone,
        customer_id=str(customer.id),
    )
    refresh_token = create_customer_refresh_token(
        phone=customer.phone,
        customer_id=str(customer.id),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "is_new_customer": False,
        "customer_id": str(customer.id),
        "full_name": customer.full_name
    }