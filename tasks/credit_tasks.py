from celery import Celery
from sqlalchemy.orm import Session
from db.database import SessionLocal
from services.credit_distribution_service import CreditDistributionService
from services.user_service import UserService
from schemas.credit_distribution import CreditDistributionCreate

# Initialize Celery
celery_app = Celery(
    "whatsapp_platform",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def distribute_credits_async(reseller_id: str, business_owner_id: str, credits: int):
    """Async task to distribute credits"""
    db = SessionLocal()
    try:
        credit_service = CreditDistributionService(db)
        distribution_data = CreditDistributionCreate(
            from_reseller_id=reseller_id,
            to_business_user_id=business_owner_id,
            credits_shared=credits
        )
        credit_service.create_credit_distribution(distribution_data)
        return {"status": "success", "message": "Credits distributed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def update_user_credits_periodically():
    """Periodic task to update user credit statistics"""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        # This could be used for monthly credit resets, interest calculations, etc.
        return {"status": "success", "message": "Credit statistics updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'update-credits-daily': {
        'task': 'tasks.credit_tasks.update_user_credits_periodically',
        'schedule': 86400.0,  # Run daily
    },
}

celery_app.conf.timezone = 'UTC'
