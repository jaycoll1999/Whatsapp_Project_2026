from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from models.credit_distribution import CreditDistribution
from models.user import User
from services.credit_distribution_service import CreditDistributionService
from schemas.credit_distribution import CreditDistributionCreate
from datetime import datetime

def create_sample_credit_distribution():
    db = SessionLocal()
    credit_service = CreditDistributionService(db)
    
    # Check if credit distribution already exists
    existing_distribution = db.query(CreditDistribution).filter(
        CreditDistribution.distribution_id == "dist-1001"
    ).first()
    if existing_distribution:
        print("Credit distribution already exists!")
        return
    
    # Check if reseller and business owner exist
    reseller = db.query(User).filter(User.user_id == "uuid-reseller-001").first()
    business_owner = db.query(User).filter(User.user_id == "uuid-business-101").first()
    
    if not reseller:
        print("Reseller not found! Please create the sample reseller first.")
        return
    
    if not business_owner:
        print("Business owner not found! Please create the sample business owner first.")
        return
    
    # Create sample credit distribution
    distribution_data = CreditDistributionCreate(
        from_reseller_id="uuid-reseller-001",
        to_business_user_id="uuid-business-101",
        credits_shared=5000
    )
    
    try:
        credit_distribution = credit_service.create_credit_distribution(distribution_data)
        
        print(f"Sample credit distribution created:")
        print(f"Distribution ID: {credit_distribution.distribution_id}")
        print(f"From Reseller ID: {credit_distribution.from_reseller_id}")
        print(f"To Business Owner ID: {credit_distribution.to_business_user_id}")
        print(f"Credits Shared: {credit_distribution.credits_shared}")
        print(f"Shared At: {credit_distribution.shared_at}")
        
        # Show updated credit stats
        reseller_stats = credit_service.get_reseller_credit_stats("uuid-reseller-001")
        business_stats = credit_service.get_business_owner_credit_stats("uuid-business-101")
        
        print(f"\nUpdated Reseller Stats:")
        print(f"  Total Credits Distributed: {reseller_stats['total_credits_distributed']}")
        print(f"  Remaining Available Credits: {reseller_stats['remaining_available_credits']}")
        print(f"  Distributions Made: {reseller_stats['distributions_made']}")
        
        print(f"\nUpdated Business Owner Stats:")
        print(f"  Total Credits Received: {business_stats['total_credits_received']}")
        print(f"  Credits Remaining: {business_stats['credits_remaining']}")
        print(f"  Distributions Received: {business_stats['distributions_received']}")
        
    except ValueError as e:
        print(f"Error creating credit distribution: {e}")
    
    db.close()

if __name__ == "__main__":
    # Create tables
    from db.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample credit distribution
    create_sample_credit_distribution()
