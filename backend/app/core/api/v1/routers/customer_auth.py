import os
import random
import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
# Import your DB utilities here
# from app.db.session import save_otp_to_db 

router = APIRouter()

class OTPRequest(BaseModel):
    phone: str
    full_name: str | None = None

@router.post("/request-otp")
async def request_otp(payload: OTPRequest):
    # 1. Generate OTP
    otp_code = str(random.randint(100000, 999999))
    
    # 2. Save to DB (You must implement this)
    # save_otp_to_db(payload.phone, otp_code)
    
    # 3. Check Environment
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        # --- DEV MODE ---
        # Do not hit Arkesel. Return the code to the frontend.
        print(f"📱 [DEV MODE] OTP for {payload.phone} is: {otp_code}")
        
        return {
            "status": "success",
            "message": "DEV MODE: SMS bypassed.",
            "is_dev_mode": True,
            "dev_otp": otp_code,
            "expires_in": 300
        }
        
    else:
        # --- PRODUCTION MODE ---
        api_key = os.getenv("ARKESEL_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMS service is not configured (Missing API Key)."
            )

        # Send via Arkesel
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://sms.arkesel.com/api/v2/sms/send",
                    headers={"api-key": api_key},
                    json={
                        "sender": "KwiqBuy",
                        "message": f"Your KwiqBuy verification code is {otp_code}. Valid for 5 minutes.",
                        "recipients": [payload.phone]
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    print(f"Arkesel Error: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Failed to send SMS. Please try again later."
                    )
                    
        except httpx.RequestError as exc:
            print(f"HTTP Request Error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMS service unreachable."
            )

        return {
            "status": "success",
            "message": "Code sent via SMS.",
            "is_dev_mode": False
        }