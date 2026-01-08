from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core import security, config
from app.schemas.token import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # MOCK AUTH for Dev Startup
    # In production, this would check the DB
    user_email = "admin@example.com"
    user_password = "password"
    
    print(f"Login attempt: username='{form_data.username}', password='{form_data.password}'")

    if form_data.username != user_email or form_data.password != user_password:
         raise HTTPException(status_code=400, detail=f"Incorrect credentials. Expected {user_email}, got {form_data.username}")

    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user_email, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
