"""
SmartPark Authentication Routes
==============================
Handles user registration, login, credential verification, and user profile retrieval.
"""

import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.models import User
from app.schemas.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse
)
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Validates input fields, verifies email format, rejects duplicate emails,
    hashes the password with bcrypt, and issues a JWT token.
    """
    clean_name = payload.full_name.strip()
    clean_email = payload.email.strip().lower()
    
    if len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 characters long."
        )

    if not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address (e.g., user@example.com)."
        )

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    # Check for duplicate email in SQLite
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in or use a different email."
        )

    # Hash password securely
    hashed_pw = hash_password(payload.password)

    # Create new user in SQLite
    new_user = User(
        full_name=clean_name,
        email=clean_email,
        hashed_password=hashed_pw,
        is_active=1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue JWT access token
    access_token = create_access_token(data={"sub": new_user.email, "uid": new_user.id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive access token"
)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Validates credentials against stored bcrypt hash and returns a JWT access token.
    """
    clean_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password. Please verify your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated."
        )

    # Issue JWT access token
    access_token = create_access_token(data={"sub": user.email, "uid": user.id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve authenticated user profile"
)
def get_authenticated_user_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the profile information of the currently authenticated user.
    Never exposes the hashed password or sensitive internals.
    """
    return UserResponse.model_validate(current_user)
