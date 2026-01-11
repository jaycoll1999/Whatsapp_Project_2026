from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.user import User
import bcrypt

def create_sample_business_owner():
    db = SessionLocal()
    
    # Check if business owner already exists
    existing_user = db.query(User).filter(User.username == "amit_store").first()
    if existing_user:
        print("Business owner already exists!")
        return
    
    # Check if reseller exists
    reseller = db.query(User).filter(User.user_id == "uuid-reseller-001").first()
    if not reseller:
        print("Reseller not found! Please create the sample reseller first.")
        return
    
    # Hash password
    password_hash = bcrypt.hashpw("business123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create sample business owner
    sample_business_owner = User(
        user_id="uuid-business-101",
        role="business_owner",
        status="active",
        parent_reseller_id="uuid-reseller-001",
        whatsapp_mode="unofficial",
        name="Amit Sharma",
        username="amit_store",
        email="amit@store.com",
        phone="+918888888888",
        password_hash=password_hash,
        business_name="Amit Electronics",
        business_description="Electronics retail shop",
        erp_system="Zoho",
        gstin="29ABCDE5678F1Z6",
        full_address="Bangalore, Karnataka",
        pincode="560001",
        country="India",
        credits_allocated=5000,
        credits_used=3200,
        credits_remaining=1800
    )
    
    db.add(sample_business_owner)
    db.commit()
    db.refresh(sample_business_owner)
    
    print(f"Sample business owner created with ID: {sample_business_owner.user_id}")
    print(f"Username: {sample_business_owner.username}")
    print(f"Password: business123")
    print(f"Role: {sample_business_owner.role}")
    print(f"Parent Reseller ID: {sample_business_owner.parent_reseller_id}")
    print(f"WhatsApp Mode: {sample_business_owner.whatsapp_mode}")
    print(f"Credits Allocated: {sample_business_owner.credits_allocated}")
    print(f"Credits Used: {sample_business_owner.credits_used}")
    print(f"Credits Remaining: {sample_business_owner.credits_remaining}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample business owner
    create_sample_business_owner()
