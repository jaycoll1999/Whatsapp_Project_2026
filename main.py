from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from db.database import engine, get_db
from models.user import User
from schemas.user import UserCreate, UserResponse, UserLogin, UserLoginResponse
from services.user_service import UserService
from typing import List
import uvicorn

# Create database tables
from db.database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WhatsApp Platform API",
    description="WhatsApp automation and messaging platform",
    version="1.0.0"
)

security = HTTPBearer()

# Dependency to get user service
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@app.get("/")
def root():
    return {"message": "WhatsApp Platform API is running"}

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, user_service: UserService = Depends(get_user_service)):
    # Check if user already exists
    existing_user = user_service.get_user_by_username(user.profile.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = user_service.get_user_by_email(user.profile.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = user_service.create_user(user)
    return UserResponse(
        user_id=db_user.user_id,
        role=db_user.role,
        status=db_user.status,
        profile={
            "name": db_user.name,
            "username": db_user.username,
            "email": db_user.email,
            "phone": db_user.phone,
            "password_hash": db_user.password_hash
        },
        business={
            "business_name": db_user.business_name,
            "business_description": db_user.business_description,
            "erp_system": db_user.erp_system,
            "gstin": db_user.gstin
        } if db_user.business_name else None,
        address={
            "full_address": db_user.full_address,
            "pincode": db_user.pincode,
            "country": db_user.country
        } if db_user.full_address else None,
        bank={
            "bank_name": db_user.bank_name
        } if db_user.bank_name else None,
        wallet={
            "total_credits": db_user.total_credits,
            "available_credits": db_user.available_credits,
            "used_credits": db_user.used_credits
        },
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

@app.get("/users/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, user_service: UserService = Depends(get_user_service)):
    users = user_service.get_users(skip=skip, limit=limit)
    return [
        UserResponse(
            user_id=user.user_id,
            role=user.role,
            status=user.status,
            profile={
                "name": user.name,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "password_hash": user.password_hash
            },
            business={
                "business_name": user.business_name,
                "business_description": user.business_description,
                "erp_system": user.erp_system,
                "gstin": user.gstin
            } if user.business_name else None,
            address={
                "full_address": user.full_address,
                "pincode": user.pincode,
                "country": user.country
            } if user.full_address else None,
            bank={
                "bank_name": user.bank_name
            } if user.bank_name else None,
            wallet={
                "total_credits": user.total_credits,
                "available_credits": user.available_credits,
                "used_credits": user.used_credits
            },
            created_at=user.created_at,
            updated_at=user.updated_at
        ) for user in users
    ]

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, user_service: UserService = Depends(get_user_service)):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        user_id=user.user_id,
        role=user.role,
        status=user.status,
        profile={
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "password_hash": user.password_hash
        },
        business={
            "business_name": user.business_name,
            "business_description": user.business_description,
            "erp_system": user.erp_system,
            "gstin": user.gstin
        } if user.business_name else None,
        address={
            "full_address": user.full_address,
            "pincode": user.pincode,
            "country": user.country
        } if user.full_address else None,
        bank={
            "bank_name": user.bank_name
        } if user.bank_name else None,
        wallet={
            "total_credits": user.total_credits,
            "available_credits": user.available_credits,
            "used_credits": user.used_credits
        },
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@app.post("/users/login", response_model=UserLoginResponse)
def login_user(user_credentials: UserLogin, user_service: UserService = Depends(get_user_service)):
    user = user_service.authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For now, return a simple token (in production, use JWT)
    access_token = f"simple_token_{user.user_id}"
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            user_id=user.user_id,
            role=user.role,
            status=user.status,
            parent_reseller_id=user.parent_reseller_id,
            whatsapp_mode=user.whatsapp_mode,
            profile={
                "name": user.name,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "password_hash": user.password_hash
            },
            business={
                "business_name": user.business_name,
                "business_description": user.business_description,
                "erp_system": user.erp_system,
                "gstin": user.gstin
            } if user.business_name else None,
            address={
                "full_address": user.full_address,
                "pincode": user.pincode,
                "country": user.country
            } if user.full_address else None,
            bank={
                "bank_name": user.bank_name
            } if user.bank_name else None,
            wallet={
                "total_credits": user.total_credits,
                "available_credits": user.available_credits,
                "used_credits": user.used_credits
            } if user.role != "business_owner" else None,
            business_owner_wallet={
                "credits_allocated": user.credits_allocated,
                "credits_used": user.credits_used,
                "credits_remaining": user.credits_remaining
            } if user.role == "business_owner" else None,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )

# Business Owner specific endpoints
@app.post("/resellers/{reseller_id}/business-owners/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_business_owner(reseller_id: str, user: UserCreate, user_service: UserService = Depends(get_user_service)):
    # Check if reseller exists
    reseller = user_service.get_user_by_id(reseller_id)
    if not reseller or reseller.role != "reseller":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseller not found"
        )
    
    # Check if user already exists
    existing_user = user_service.get_user_by_username(user.profile.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = user_service.get_user_by_email(user.profile.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = user_service.create_business_owner(user, reseller_id)
    return UserResponse(
        user_id=db_user.user_id,
        role=db_user.role,
        status=db_user.status,
        parent_reseller_id=db_user.parent_reseller_id,
        whatsapp_mode=db_user.whatsapp_mode,
        profile={
            "name": db_user.name,
            "username": db_user.username,
            "email": db_user.email,
            "phone": db_user.phone,
            "password_hash": db_user.password_hash
        },
        business={
            "business_name": db_user.business_name,
            "business_description": db_user.business_description,
            "erp_system": db_user.erp_system,
            "gstin": db_user.gstin
        } if db_user.business_name else None,
        address={
            "full_address": db_user.full_address,
            "pincode": db_user.pincode,
            "country": db_user.country
        } if db_user.full_address else None,
        bank={
            "bank_name": db_user.bank_name
        } if db_user.bank_name else None,
        wallet=None,
        business_owner_wallet={
            "credits_allocated": db_user.credits_allocated,
            "credits_used": db_user.credits_used,
            "credits_remaining": db_user.credits_remaining
        },
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )

@app.get("/resellers/{reseller_id}/business-owners/", response_model=List[UserResponse])
def get_business_owners_by_reseller(reseller_id: str, skip: int = 0, limit: int = 100, user_service: UserService = Depends(get_user_service)):
    # Check if reseller exists
    reseller = user_service.get_user_by_id(reseller_id)
    if not reseller or reseller.role != "reseller":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseller not found"
        )
    
    business_owners = user_service.get_business_owners_by_reseller(reseller_id, skip, limit)
    return [
        UserResponse(
            user_id=user.user_id,
            role=user.role,
            status=user.status,
            parent_reseller_id=user.parent_reseller_id,
            whatsapp_mode=user.whatsapp_mode,
            profile={
                "name": user.name,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "password_hash": user.password_hash
            },
            business={
                "business_name": user.business_name,
                "business_description": user.business_description,
                "erp_system": user.erp_system,
                "gstin": user.gstin
            } if user.business_name else None,
            address={
                "full_address": user.full_address,
                "pincode": user.pincode,
                "country": user.country
            } if user.full_address else None,
            bank={
                "bank_name": user.bank_name
            } if user.bank_name else None,
            wallet=None,
            business_owner_wallet={
                "credits_allocated": user.credits_allocated,
                "credits_used": user.credits_used,
                "credits_remaining": user.credits_remaining
            },
            created_at=user.created_at,
            updated_at=user.updated_at
        ) for user in business_owners
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)