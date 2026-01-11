from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreditDistributionCreate(BaseModel):
    from_reseller_id: str
    to_business_user_id: str
    credits_shared: int = Field(..., gt=0, description="Credits must be greater than 0")

class CreditDistributionResponse(BaseModel):
    distribution_id: str
    from_reseller_id: str
    to_business_user_id: str
    credits_shared: int
    shared_at: datetime
    
    class Config:
        from_attributes = True

class CreditDistributionSummary(BaseModel):
    total_distributed: int
    total_distributions: int
    average_distribution: float

class ResellerCreditStats(BaseModel):
    reseller_id: str
    total_credits_distributed: int
    total_business_owners: int
    remaining_available_credits: int
    distributions_made: int

class BusinessOwnerCreditStats(BaseModel):
    business_user_id: str
    total_credits_received: int
    credits_used: int
    credits_remaining: int
    distributions_received: int
