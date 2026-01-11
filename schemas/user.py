from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserProfile(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: str
    password_hash: str

class BusinessInfo(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    erp_system: Optional[str] = None
    gstin: Optional[str] = None

class Address(BaseModel):
    full_address: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"

class BankInfo(BaseModel):
    bank_name: Optional[str] = None

class Wallet(BaseModel):
    total_credits: int = 0
    available_credits: int = 0
    used_credits: int = 0

class BusinessOwnerWallet(BaseModel):
    credits_allocated: int = 0
    credits_used: int = 0
    credits_remaining: int = 0

class UserCreate(BaseModel):
    role: str = "platform_user"
    parent_reseller_id: Optional[str] = None
    whatsapp_mode: str = "official"
    profile: UserProfile
    business: Optional[BusinessInfo] = None
    address: Optional[Address] = None
    bank: Optional[BankInfo] = None
    wallet: Optional[Wallet] = None
    business_owner_wallet: Optional[BusinessOwnerWallet] = None

class UserUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None
    parent_reseller_id: Optional[str] = None
    whatsapp_mode: Optional[str] = None
    profile: Optional[UserProfile] = None
    business: Optional[BusinessInfo] = None
    address: Optional[Address] = None
    bank: Optional[BankInfo] = None
    wallet: Optional[Wallet] = None
    business_owner_wallet: Optional[BusinessOwnerWallet] = None

class UserResponse(BaseModel):
    user_id: str
    role: str
    status: str
    parent_reseller_id: Optional[str] = None
    whatsapp_mode: str = "official"
    profile: UserProfile
    business: Optional[BusinessInfo] = None
    address: Optional[Address] = None
    bank: Optional[BankInfo] = None
    wallet: Optional[Wallet] = None
    business_owner_wallet: Optional[BusinessOwnerWallet] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
