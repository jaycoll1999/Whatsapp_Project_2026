from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.user import User
import bcrypt

def create_sample_user():
    db = SessionLocal()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == "mayur_admin").first()
    if existing_user:
        print("User already exists!")
        return
    
    # Hash password
    password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create sample user
    sample_user = User(
        user_id="uuid-reseller-001",
        role="reseller",
        status="active",
        name="Mayur Khalate",
        username="mayur_admin",
        email="mayur@platform.com",
        phone="+919999999999",
        password_hash=password_hash,
        business_name="MK WhatsApp Services",
        business_description="WhatsApp automation and messaging platform",
        erp_system="Tally",
        gstin="27ABCDE1234F1Z5",
        full_address="Pune, Maharashtra",
        pincode="411001",
        country="India",
        bank_name="HDFC Bank",
        total_credits=100000,
        available_credits=75000,
        used_credits=25000
    )
    
    db.add(sample_user)
    db.commit()
    db.refresh(sample_user)
    
    print(f"Sample user created with ID: {sample_user.user_id}")
    print(f"Username: {sample_user.username}")
    print(f"Password: admin123")
    print(f"Role: {sample_user.role}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample user
    create_sample_user()
