from sqlalchemy.orm import Session
from models.credit_distribution import CreditDistribution
from models.user import User
from schemas.credit_distribution import CreditDistributionCreate, CreditDistributionResponse
from typing import Optional, List
from datetime import datetime

class CreditDistributionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_credit_distribution(self, distribution_data: CreditDistributionCreate) -> Optional[CreditDistribution]:
        # Validate reseller exists and has sufficient credits
        reseller = self.db.query(User).filter(
            User.user_id == distribution_data.from_reseller_id,
            User.role == "reseller"
        ).first()
        
        if not reseller:
            raise ValueError("Reseller not found")
        
        if reseller.available_credits < distribution_data.credits_shared:
            raise ValueError("Insufficient credits available")
        
        # Validate business owner exists and belongs to this reseller
        business_owner = self.db.query(User).filter(
            User.user_id == distribution_data.to_business_user_id,
            User.role == "business_owner",
            User.parent_reseller_id == distribution_data.from_reseller_id
        ).first()
        
        if not business_owner:
            raise ValueError("Business owner not found or does not belong to this reseller")
        
        # Create credit distribution record
        credit_distribution = CreditDistribution(
            from_reseller_id=distribution_data.from_reseller_id,
            to_business_user_id=distribution_data.to_business_user_id,
            credits_shared=distribution_data.credits_shared
        )
        
        # Update reseller credits
        reseller.available_credits -= distribution_data.credits_shared
        reseller.used_credits += distribution_data.credits_shared
        
        # Update business owner credits
        business_owner.credits_allocated += distribution_data.credits_shared
        business_owner.credits_remaining += distribution_data.credits_shared
        
        self.db.add(credit_distribution)
        self.db.commit()
        self.db.refresh(credit_distribution)
        
        return credit_distribution
    
    def get_distribution_by_id(self, distribution_id: str) -> Optional[CreditDistribution]:
        return self.db.query(CreditDistribution).filter(
            CreditDistribution.distribution_id == distribution_id
        ).first()
    
    def get_distributions_by_reseller(self, reseller_id: str, skip: int = 0, limit: int = 100) -> List[CreditDistribution]:
        return self.db.query(CreditDistribution).filter(
            CreditDistribution.from_reseller_id == reseller_id
        ).offset(skip).limit(limit).all()
    
    def get_distributions_by_business_owner(self, business_user_id: str, skip: int = 0, limit: int = 100) -> List[CreditDistribution]:
        return self.db.query(CreditDistribution).filter(
            CreditDistribution.to_business_user_id == business_user_id
        ).offset(skip).limit(limit).all()
    
    def get_all_distributions(self, skip: int = 0, limit: int = 100) -> List[CreditDistribution]:
        return self.db.query(CreditDistribution).offset(skip).limit(limit).all()
    
    def get_reseller_credit_stats(self, reseller_id: str) -> Optional[dict]:
        reseller = self.db.query(User).filter(
            User.user_id == reseller_id,
            User.role == "reseller"
        ).first()
        
        if not reseller:
            return None
        
        total_distributed = self.db.query(CreditDistribution).filter(
            CreditDistribution.from_reseller_id == reseller_id
        ).with_entities(
            self.db.func.sum(CreditDistribution.credits_shared)
        ).scalar() or 0
        
        total_business_owners = self.db.query(User).filter(
            User.parent_reseller_id == reseller_id,
            User.role == "business_owner"
        ).count()
        
        distributions_made = self.db.query(CreditDistribution).filter(
            CreditDistribution.from_reseller_id == reseller_id
        ).count()
        
        return {
            "reseller_id": reseller_id,
            "total_credits_distributed": total_distributed,
            "total_business_owners": total_business_owners,
            "remaining_available_credits": reseller.available_credits,
            "distributions_made": distributions_made
        }
    
    def get_business_owner_credit_stats(self, business_user_id: str) -> Optional[dict]:
        business_owner = self.db.query(User).filter(
            User.user_id == business_user_id,
            User.role == "business_owner"
        ).first()
        
        if not business_owner:
            return None
        
        total_received = self.db.query(CreditDistribution).filter(
            CreditDistribution.to_business_user_id == business_user_id
        ).with_entities(
            self.db.func.sum(CreditDistribution.credits_shared)
        ).scalar() or 0
        
        distributions_received = self.db.query(CreditDistribution).filter(
            CreditDistribution.to_business_user_id == business_user_id
        ).count()
        
        return {
            "business_user_id": business_user_id,
            "total_credits_received": total_received,
            "credits_used": business_owner.credits_used,
            "credits_remaining": business_owner.credits_remaining,
            "distributions_received": distributions_received
        }
    
    def get_distribution_summary(self) -> dict:
        total_distributed = self.db.query(CreditDistribution).with_entities(
            self.db.func.sum(CreditDistribution.credits_shared)
        ).scalar() or 0
        
        total_distributions = self.db.query(CreditDistribution).count()
        
        average_distribution = total_distributed / total_distributions if total_distributions > 0 else 0
        
        return {
            "total_distributed": total_distributed,
            "total_distributions": total_distributions,
            "average_distribution": average_distribution
        }
