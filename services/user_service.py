from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate
from typing import Optional, List
from datetime import datetime
import bcrypt

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, user_data: UserCreate) -> User:
        # Hash password
        password_hash = bcrypt.hashpw(user_data.profile.password_hash.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        db_user = User(
            role=user_data.role,
            parent_reseller_id=user_data.parent_reseller_id,
            whatsapp_mode=user_data.whatsapp_mode,
            name=user_data.profile.name,
            username=user_data.profile.username,
            email=user_data.profile.email,
            phone=user_data.profile.phone,
            password_hash=password_hash,
            business_name=user_data.business.business_name if user_data.business else None,
            business_description=user_data.business.business_description if user_data.business else None,
            erp_system=user_data.business.erp_system if user_data.business else None,
            gstin=user_data.business.gstin if user_data.business else None,
            full_address=user_data.address.full_address if user_data.address else None,
            pincode=user_data.address.pincode if user_data.address else None,
            country=user_data.address.country if user_data.address else "India",
            bank_name=user_data.bank.bank_name if user_data.bank else None,
            total_credits=user_data.wallet.total_credits if user_data.wallet else 0,
            available_credits=user_data.wallet.available_credits if user_data.wallet else 0,
            used_credits=user_data.wallet.used_credits if user_data.wallet else 0,
            credits_allocated=user_data.business_owner_wallet.credits_allocated if user_data.business_owner_wallet else 0,
            credits_used=user_data.business_owner_wallet.credits_used if user_data.business_owner_wallet else 0,
            credits_remaining=user_data.business_owner_wallet.credits_remaining if user_data.business_owner_wallet else 0,
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "profile" and value:
                for profile_field, profile_value in value.items():
                    if profile_field == "password_hash":
                        # Hash new password
                        profile_value = bcrypt.hashpw(profile_value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    setattr(db_user, profile_field, profile_value)
            elif field == "business" and value:
                for business_field, business_value in value.items():
                    setattr(db_user, business_field, business_value)
            elif field == "address" and value:
                for address_field, address_value in value.items():
                    setattr(db_user, address_field, address_value)
            elif field == "bank" and value:
                for bank_field, bank_value in value.items():
                    setattr(db_user, bank_field, bank_value)
            elif field == "wallet" and value:
                for wallet_field, wallet_value in value.items():
                    setattr(db_user, wallet_field, wallet_value)
            elif field == "business_owner_wallet" and value:
                for bo_wallet_field, bo_wallet_value in value.items():
                    setattr(db_user, bo_wallet_field, bo_wallet_value)
            else:
                setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete_user(self, user_id: str) -> bool:
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user
        return None
    
    def get_business_owners_by_reseller(self, reseller_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).filter(User.parent_reseller_id == reseller_id).offset(skip).limit(limit).all()
    
    def create_business_owner(self, user_data: UserCreate, reseller_id: str) -> User:
        # Set parent reseller and role
        user_data.parent_reseller_id = reseller_id
        user_data.role = "business_owner"
        
        return self.create_user(user_data)
