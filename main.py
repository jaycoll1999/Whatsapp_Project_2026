from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from db.database import engine, get_db
from models.user import User
from models.credit_distribution import CreditDistribution
from models.message import Message
from models.unofficial_device import UnofficialLinkedDevice
from models.device_session import DeviceSession
from models.message_usage_log import MessageUsageLog
from models.reseller_analytics import ResellerAnalytics
from schemas.user import UserCreate, UserResponse, UserLogin, UserLoginResponse
from schemas.credit_distribution import CreditDistributionCreate, CreditDistributionResponse, ResellerCreditStats, BusinessOwnerCreditStats
from schemas.message import MessageCreate, MessageResponse, MessageSendRequest, BulkMessageRequest, MessageStats, WebhookPayload
from schemas.unofficial_device import (
    UnofficialDeviceCreate, UnofficialDeviceUpdate, UnofficialDeviceResponse,
    QRCodeRequest, QRCodeResponse, DeviceConnectRequest, DeviceConnectResponse,
    DeviceDisconnectRequest, DeviceDisconnectResponse, DeviceStatusUpdate,
    DeviceStats, UserDeviceStats, BulkDeviceOperation, DeviceHealthCheck
)
from schemas.device_session import (
    DeviceSessionCreate, DeviceSessionUpdate, DeviceSessionResponse,
    SessionCreateRequest, SessionCreateResponse, SessionValidateRequest, SessionValidateResponse,
    SessionExtendRequest, SessionExtendResponse, SessionRevokeRequest, SessionRevokeResponse,
    SessionLoginRequest, SessionLoginResponse, SessionActivityUpdate,
    SessionStats, DeviceSessionStats, UserSessionStats, SessionSecurityCheck,
    BulkSessionOperation, SessionCleanupRequest, SessionCleanupResponse,
    SessionHealthCheck
)
from schemas.message_usage_log import (
    MessageUsageLogCreate, MessageUsageLogUpdate, MessageUsageLogResponse,
    UsageLogCreateRequest, UsageLogCreateResponse, UsageLogRefundRequest, UsageLogRefundResponse,
    UsageLogUpdateRequest, UsageLogUpdateResponse, UsageStats, UserUsageStats,
    DeviceUsageStats, SessionUsageStats, UsageAnalytics, UsageFilter,
    BulkUsageOperation, BulkUsageResponse, UsageCleanupRequest, UsageCleanupResponse
)
from schemas.reseller_analytics import (
    ResellerAnalyticsResponse, AnalyticsData, BusinessUserStats,
    CreateAnalyticsRequest, UpdateAnalyticsRequest,
    CreateBusinessUserStatsRequest, UpdateBusinessUserStatsRequest,
    AnalyticsFilter, AnalyticsSummary, ResellerPerformanceMetrics,
    TopPerformersResponse, AnalyticsTrends, AnalyticsComparison,
    AnalyticsExportRequest, AnalyticsExportResponse,
    AnalyticsHealthCheck, AnalyticsCleanupRequest, AnalyticsCleanupResponse
)
from services.user_service import UserService
from services.credit_distribution_service import CreditDistributionService
from services.message_service import MessageService
from services.unofficial_device_service import UnofficialDeviceService
from services.device_session_service import DeviceSessionService
from services.message_usage_log_service import MessageUsageLogService
from services.reseller_analytics_service import ResellerAnalyticsService
from typing import List, Optional
from datetime import datetime
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

# Dependency to get credit distribution service
def get_credit_distribution_service(db: Session = Depends(get_db)) -> CreditDistributionService:
    return CreditDistributionService(db)

# Dependency to get message service
def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    return MessageService(db)

# Dependency to get unofficial device service
def get_unofficial_device_service(db: Session = Depends(get_db)) -> UnofficialDeviceService:
    return UnofficialDeviceService(db)

# Dependency to get device session service
def get_device_session_service(db: Session = Depends(get_db)) -> DeviceSessionService:
    return DeviceSessionService(db)

# Dependency to get message usage log service
def get_message_usage_log_service(db: Session = Depends(get_db)) -> MessageUsageLogService:
    return MessageUsageLogService(db)

# Dependency to get reseller analytics service
def get_reseller_analytics_service(db: Session = Depends(get_db)) -> ResellerAnalyticsService:
    return ResellerAnalyticsService(db)

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

# Credit Distribution endpoints
@app.post("/credit-distributions/", response_model=CreditDistributionResponse, status_code=status.HTTP_201_CREATED)
def create_credit_distribution(
    distribution: CreditDistributionCreate,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    try:
        credit_distribution = credit_service.create_credit_distribution(distribution)
        return CreditDistributionResponse(
            distribution_id=credit_distribution.distribution_id,
            from_reseller_id=credit_distribution.from_reseller_id,
            to_business_user_id=credit_distribution.to_business_user_id,
            credits_shared=credit_distribution.credits_shared,
            shared_at=credit_distribution.shared_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/credit-distributions/", response_model=List[CreditDistributionResponse])
def get_all_credit_distributions(
    skip: int = 0,
    limit: int = 100,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    distributions = credit_service.get_all_distributions(skip, limit)
    return [
        CreditDistributionResponse(
            distribution_id=distribution.distribution_id,
            from_reseller_id=distribution.from_reseller_id,
            to_business_user_id=distribution.to_business_user_id,
            credits_shared=distribution.credits_shared,
            shared_at=distribution.shared_at
        ) for distribution in distributions
    ]

@app.get("/credit-distributions/{distribution_id}", response_model=CreditDistributionResponse)
def get_credit_distribution(
    distribution_id: str,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    distribution = credit_service.get_distribution_by_id(distribution_id)
    if not distribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit distribution not found"
        )
    
    return CreditDistributionResponse(
        distribution_id=distribution.distribution_id,
        from_reseller_id=distribution.from_reseller_id,
        to_business_user_id=distribution.to_business_user_id,
        credits_shared=distribution.credits_shared,
        shared_at=distribution.shared_at
    )

@app.get("/resellers/{reseller_id}/credit-distributions/", response_model=List[CreditDistributionResponse])
def get_credit_distributions_by_reseller(
    reseller_id: str,
    skip: int = 0,
    limit: int = 100,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    distributions = credit_service.get_distributions_by_reseller(reseller_id, skip, limit)
    return [
        CreditDistributionResponse(
            distribution_id=distribution.distribution_id,
            from_reseller_id=distribution.from_reseller_id,
            to_business_user_id=distribution.to_business_user_id,
            credits_shared=distribution.credits_shared,
            shared_at=distribution.shared_at
        ) for distribution in distributions
    ]

@app.get("/business-owners/{business_user_id}/credit-distributions/", response_model=List[CreditDistributionResponse])
def get_credit_distributions_by_business_owner(
    business_user_id: str,
    skip: int = 0,
    limit: int = 100,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    distributions = credit_service.get_distributions_by_business_owner(business_user_id, skip, limit)
    return [
        CreditDistributionResponse(
            distribution_id=distribution.distribution_id,
            from_reseller_id=distribution.from_reseller_id,
            to_business_user_id=distribution.to_business_user_id,
            credits_shared=distribution.credits_shared,
            shared_at=distribution.shared_at
        ) for distribution in distributions
    ]

@app.get("/resellers/{reseller_id}/credit-stats/", response_model=ResellerCreditStats)
def get_reseller_credit_stats(
    reseller_id: str,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    stats = credit_service.get_reseller_credit_stats(reseller_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseller not found"
        )
    
    return ResellerCreditStats(**stats)

@app.get("/business-owners/{business_user_id}/credit-stats/", response_model=BusinessOwnerCreditStats)
def get_business_owner_credit_stats(
    business_user_id: str,
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    stats = credit_service.get_business_owner_credit_stats(business_user_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business owner not found"
        )
    
    return BusinessOwnerCreditStats(**stats)

@app.get("/credit-distributions/summary/")
def get_credit_distribution_summary(
    credit_service: CreditDistributionService = Depends(get_credit_distribution_service)
):
    return credit_service.get_distribution_summary()

# Message endpoints
@app.post("/messages/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message: MessageCreate,
    message_service: MessageService = Depends(get_message_service)
):
    try:
        db_message = message_service.create_message(message)
        return MessageResponse(
            message_id=db_message.message_id,
            user_id=db_message.user_id,
            channel=db_message.channel,
            mode=db_message.mode,
            sender_number=db_message.sender_number,
            receiver_number=db_message.receiver_number,
            message_type=db_message.message_type,
            template_name=db_message.template_name,
            message_body=db_message.message_body,
            status=db_message.status,
            credits_used=db_message.credits_used,
            sent_at=db_message.sent_at,
            delivered_at=db_message.delivered_at,
            read_at=db_message.read_at,
            error_message=db_message.error_message,
            external_message_id=db_message.external_message_id,
            retry_count=db_message.retry_count,
            max_retries=db_message.max_retries
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/users/{user_id}/send-message/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    user_id: str,
    message_request: MessageSendRequest,
    message_service: MessageService = Depends(get_message_service)
):
    try:
        db_message = message_service.send_message(user_id, message_request)
        return MessageResponse(
            message_id=db_message.message_id,
            user_id=db_message.user_id,
            channel=db_message.channel,
            mode=db_message.mode,
            sender_number=db_message.sender_number,
            receiver_number=db_message.receiver_number,
            message_type=db_message.message_type,
            template_name=db_message.template_name,
            message_body=db_message.message_body,
            status=db_message.status,
            credits_used=db_message.credits_used,
            sent_at=db_message.sent_at,
            delivered_at=db_message.delivered_at,
            read_at=db_message.read_at,
            error_message=db_message.error_message,
            external_message_id=db_message.external_message_id,
            retry_count=db_message.retry_count,
            max_retries=db_message.max_retries
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/users/{user_id}/send-bulk-messages/", response_model=List[MessageResponse])
def send_bulk_messages(
    user_id: str,
    bulk_request: BulkMessageRequest,
    message_service: MessageService = Depends(get_message_service)
):
    try:
        messages = message_service.send_bulk_messages(user_id, bulk_request)
        return [
            MessageResponse(
                message_id=msg.message_id,
                user_id=msg.user_id,
                channel=msg.channel,
                mode=msg.mode,
                sender_number=msg.sender_number,
                receiver_number=msg.receiver_number,
                message_type=msg.message_type,
                template_name=msg.template_name,
                message_body=msg.message_body,
                status=msg.status,
                credits_used=msg.credits_used,
                sent_at=msg.sent_at,
                delivered_at=msg.delivered_at,
                read_at=msg.read_at,
                error_message=msg.error_message,
                external_message_id=msg.external_message_id,
                retry_count=msg.retry_count,
                max_retries=msg.max_retries
            ) for msg in messages
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/messages/", response_model=List[MessageResponse])
def get_all_messages(
    skip: int = 0,
    limit: int = 100,
    message_service: MessageService = Depends(get_message_service)
):
    messages = message_service.get_all_messages(skip, limit)
    return [
        MessageResponse(
            message_id=msg.message_id,
            user_id=msg.user_id,
            channel=msg.channel,
            mode=msg.mode,
            sender_number=msg.sender_number,
            receiver_number=msg.receiver_number,
            message_type=msg.message_type,
            template_name=msg.template_name,
            message_body=msg.message_body,
            status=msg.status,
            credits_used=msg.credits_used,
            sent_at=msg.sent_at,
            delivered_at=msg.delivered_at,
            read_at=msg.read_at,
            error_message=msg.error_message,
            external_message_id=msg.external_message_id,
            retry_count=msg.retry_count,
            max_retries=msg.max_retries
        ) for msg in messages
    ]

@app.get("/messages/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: str,
    message_service: MessageService = Depends(get_message_service)
):
    message = message_service.get_message_by_id(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return MessageResponse(
        message_id=message.message_id,
        user_id=message.user_id,
        channel=message.channel,
        mode=message.mode,
        sender_number=message.sender_number,
        receiver_number=message.receiver_number,
        message_type=message.message_type,
        template_name=message.template_name,
        message_body=message.message_body,
        status=message.status,
        credits_used=message.credits_used,
        sent_at=message.sent_at,
        delivered_at=message.delivered_at,
        read_at=message.read_at,
        error_message=message.error_message,
        external_message_id=message.external_message_id,
        retry_count=message.retry_count,
        max_retries=message.max_retries
    )

@app.get("/users/{user_id}/messages/", response_model=List[MessageResponse])
def get_user_messages(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    message_service: MessageService = Depends(get_message_service)
):
    messages = message_service.get_messages_by_user(user_id, skip, limit)
    return [
        MessageResponse(
            message_id=msg.message_id,
            user_id=msg.user_id,
            channel=msg.channel,
            mode=msg.mode,
            sender_number=msg.sender_number,
            receiver_number=msg.receiver_number,
            message_type=msg.message_type,
            template_name=msg.template_name,
            message_body=msg.message_body,
            status=msg.status,
            credits_used=msg.credits_used,
            sent_at=msg.sent_at,
            delivered_at=msg.delivered_at,
            read_at=msg.read_at,
            error_message=msg.error_message,
            external_message_id=msg.external_message_id,
            retry_count=msg.retry_count,
            max_retries=msg.max_retries
        ) for msg in messages
    ]

@app.get("/messages/status/{status}", response_model=List[MessageResponse])
def get_messages_by_status(
    status: str,
    skip: int = 0,
    limit: int = 100,
    message_service: MessageService = Depends(get_message_service)
):
    messages = message_service.get_messages_by_status(status, skip, limit)
    return [
        MessageResponse(
            message_id=msg.message_id,
            user_id=msg.user_id,
            channel=msg.channel,
            mode=msg.mode,
            sender_number=msg.sender_number,
            receiver_number=msg.receiver_number,
            message_type=msg.message_type,
            template_name=msg.template_name,
            message_body=msg.message_body,
            status=msg.status,
            credits_used=msg.credits_used,
            sent_at=msg.sent_at,
            delivered_at=msg.delivered_at,
            read_at=msg.read_at,
            error_message=msg.error_message,
            external_message_id=msg.external_message_id,
            retry_count=msg.retry_count,
            max_retries=msg.max_retries
        ) for msg in messages
    ]

@app.post("/messages/retry-failed/")
def retry_failed_messages(
    max_retries: int = 3,
    message_service: MessageService = Depends(get_message_service)
):
    retried_messages = message_service.retry_failed_messages(max_retries)
    return {
        "retried_count": len(retried_messages),
        "message_ids": [msg.message_id for msg in retried_messages]
    }

@app.get("/users/{user_id}/message-stats/", response_model=MessageStats)
def get_user_message_stats(
    user_id: str,
    message_service: MessageService = Depends(get_message_service)
):
    return message_service.get_message_stats(user_id)

@app.get("/message-stats/", response_model=MessageStats)
def get_global_message_stats(
    message_service: MessageService = Depends(get_message_service)
):
    return message_service.get_message_stats()

@app.post("/webhooks/whatsapp/{message_id}")
def process_whatsapp_webhook(
    message_id: str,
    webhook_data: WebhookPayload,
    message_service: MessageService = Depends(get_message_service)
):
    message = message_service.process_webhook(message_id, webhook_data.dict())
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return {"status": "success", "message": "Webhook processed successfully"}

# Unofficial Linked Device endpoints
@app.post("/unofficial-devices/", response_model=UnofficialDeviceResponse, status_code=status.HTTP_201_CREATED)
def create_unofficial_device(
    device: UnofficialDeviceCreate,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        db_device = device_service.create_device(device)
        return UnofficialDeviceResponse(
            device_id=db_device.device_id,
            user_id=db_device.user_id,
            device_name=db_device.device_name,
            device_type=db_device.device_type,
            device_os=db_device.device_os,
            browser_info=db_device.browser_info,
            session_status=db_device.session_status,
            qr_code_data=db_device.qr_code_data,
            qr_last_generated=db_device.qr_last_generated,
            qr_expires_at=db_device.qr_expires_at,
            ip_address=db_device.ip_address,
            user_agent=db_device.user_agent,
            connection_string=db_device.connection_string,
            last_active=db_device.last_active,
            last_message_sent=db_device.last_message_sent,
            last_message_received=db_device.last_message_received,
            messages_sent=db_device.messages_sent,
            messages_received=db_device.messages_received,
            total_activity_time=db_device.total_activity_time,
            is_active=db_device.is_active,
            max_daily_messages=db_device.max_daily_messages,
            daily_message_count=db_device.daily_message_count,
            last_reset_date=db_device.last_reset_date,
            last_error=db_device.last_error,
            error_count=db_device.error_count,
            reconnect_attempts=db_device.reconnect_attempts,
            max_reconnect_attempts=db_device.max_reconnect_attempts,
            created_at=db_device.created_at,
            updated_at=db_device.updated_at,
            last_connected_at=db_device.last_connected_at,
            last_disconnected_at=db_device.last_disconnected_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/unofficial-devices/", response_model=List[UnofficialDeviceResponse])
def get_all_unofficial_devices(
    skip: int = 0,
    limit: int = 100,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    devices = device_service.get_all_devices(skip, limit)
    return [
        UnofficialDeviceResponse(
            device_id=device.device_id,
            user_id=device.user_id,
            device_name=device.device_name,
            device_type=device.device_type,
            device_os=device.device_os,
            browser_info=device.browser_info,
            session_status=device.session_status,
            qr_code_data=device.qr_code_data,
            qr_last_generated=device.qr_last_generated,
            qr_expires_at=device.qr_expires_at,
            ip_address=device.ip_address,
            user_agent=device.user_agent,
            connection_string=device.connection_string,
            last_active=device.last_active,
            last_message_sent=device.last_message_sent,
            last_message_received=device.last_message_received,
            messages_sent=device.messages_sent,
            messages_received=device.messages_received,
            total_activity_time=device.total_activity_time,
            is_active=device.is_active,
            max_daily_messages=device.max_daily_messages,
            daily_message_count=device.daily_message_count,
            last_reset_date=device.last_reset_date,
            last_error=device.last_error,
            error_count=device.error_count,
            reconnect_attempts=device.reconnect_attempts,
            max_reconnect_attempts=device.max_reconnect_attempts,
            created_at=device.created_at,
            updated_at=device.updated_at,
            last_connected_at=device.last_connected_at,
            last_disconnected_at=device.last_disconnected_at
        ) for device in devices
    ]

@app.get("/unofficial-devices/{device_id}", response_model=UnofficialDeviceResponse)
def get_unofficial_device(
    device_id: str,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    device = device_service.get_device_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return UnofficialDeviceResponse(
        device_id=device.device_id,
        user_id=device.user_id,
        device_name=device.device_name,
        device_type=device.device_type,
        device_os=device.device_os,
        browser_info=device.browser_info,
        session_status=device.session_status,
        qr_code_data=device.qr_code_data,
        qr_last_generated=device.qr_last_generated,
        qr_expires_at=device.qr_expires_at,
        ip_address=device.ip_address,
        user_agent=device.user_agent,
        connection_string=device.connection_string,
        last_active=device.last_active,
        last_message_sent=device.last_message_sent,
        last_message_received=device.last_message_received,
        messages_sent=device.messages_sent,
        messages_received=device.messages_received,
        total_activity_time=device.total_activity_time,
        is_active=device.is_active,
        max_daily_messages=device.max_daily_messages,
        daily_message_count=device.daily_message_count,
        last_reset_date=device.last_reset_date,
        last_error=device.last_error,
        error_count=device.error_count,
        reconnect_attempts=device.reconnect_attempts,
        max_reconnect_attempts=device.max_reconnect_attempts,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_connected_at=device.last_connected_at,
        last_disconnected_at=device.last_disconnected_at
    )

@app.get("/users/{user_id}/unofficial-devices/", response_model=List[UnofficialDeviceResponse])
def get_user_unofficial_devices(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    devices = device_service.get_devices_by_user(user_id, skip, limit)
    return [
        UnofficialDeviceResponse(
            device_id=device.device_id,
            user_id=device.user_id,
            device_name=device.device_name,
            device_type=device.device_type,
            device_os=device.device_os,
            browser_info=device.browser_info,
            session_status=device.session_status,
            qr_code_data=device.qr_code_data,
            qr_last_generated=device.qr_last_generated,
            qr_expires_at=device.qr_expires_at,
            ip_address=device.ip_address,
            user_agent=device.user_agent,
            connection_string=device.connection_string,
            last_active=device.last_active,
            last_message_sent=device.last_message_sent,
            last_message_received=device.last_message_received,
            messages_sent=device.messages_sent,
            messages_received=device.messages_received,
            total_activity_time=device.total_activity_time,
            is_active=device.is_active,
            max_daily_messages=device.max_daily_messages,
            daily_message_count=device.daily_message_count,
            last_reset_date=device.last_reset_date,
            last_error=device.last_error,
            error_count=device.error_count,
            reconnect_attempts=device.reconnect_attempts,
            max_reconnect_attempts=device.max_reconnect_attempts,
            created_at=device.created_at,
            updated_at=device.updated_at,
            last_connected_at=device.last_connected_at,
            last_disconnected_at=device.last_disconnected_at
        ) for device in devices
    ]

@app.put("/unofficial-devices/{device_id}", response_model=UnofficialDeviceResponse)
def update_unofficial_device(
    device_id: str,
    update_data: UnofficialDeviceUpdate,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    device = device_service.update_device(device_id, update_data)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return UnofficialDeviceResponse(
        device_id=device.device_id,
        user_id=device.user_id,
        device_name=device.device_name,
        device_type=device.device_type,
        device_os=device.device_os,
        browser_info=device.browser_info,
        session_status=device.session_status,
        qr_code_data=device.qr_code_data,
        qr_last_generated=device.qr_last_generated,
        qr_expires_at=device.qr_expires_at,
        ip_address=device.ip_address,
        user_agent=device.user_agent,
        connection_string=device.connection_string,
        last_active=device.last_active,
        last_message_sent=device.last_message_sent,
        last_message_received=device.last_message_received,
        messages_sent=device.messages_sent,
        messages_received=device.messages_received,
        total_activity_time=device.total_activity_time,
        is_active=device.is_active,
        max_daily_messages=device.max_daily_messages,
        daily_message_count=device.daily_message_count,
        last_reset_date=device.last_reset_date,
        last_error=device.last_error,
        error_count=device.error_count,
        reconnect_attempts=device.reconnect_attempts,
        max_reconnect_attempts=device.max_reconnect_attempts,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_connected_at=device.last_connected_at,
        last_disconnected_at=device.last_disconnected_at
    )

@app.delete("/unofficial-devices/{device_id}")
def delete_unofficial_device(
    device_id: str,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    success = device_service.delete_device(device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {"message": "Device deleted successfully"}

@app.post("/unofficial-devices/{device_id}/generate-qr/", response_model=QRCodeResponse)
def generate_device_qr_code(
    device_id: str,
    regenerate: bool = False,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        return device_service.generate_qr_code(device_id, regenerate)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/unofficial-devices/connect/", response_model=DeviceConnectResponse)
def connect_unofficial_device(
    connect_request: DeviceConnectRequest,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        return device_service.connect_device(connect_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/unofficial-devices/disconnect/", response_model=DeviceDisconnectResponse)
def disconnect_unofficial_device(
    disconnect_request: DeviceDisconnectRequest,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        return device_service.disconnect_device(disconnect_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/unofficial-devices/update-status/")
def update_device_status(
    status_update: DeviceStatusUpdate,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        device_service.update_device_status(status_update)
        return {"status": "success", "message": "Device status updated successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/unofficial-devices/{device_id}/stats/", response_model=DeviceStats)
def get_device_stats(
    device_id: str,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        return device_service.get_device_stats(device_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@app.get("/users/{user_id}/unofficial-devices/stats/", response_model=UserDeviceStats)
def get_user_device_stats(
    user_id: str,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    return device_service.get_user_device_stats(user_id)

@app.post("/unofficial-devices/bulk-operation/")
def bulk_device_operation(
    operation: BulkDeviceOperation,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    return device_service.bulk_device_operation(operation)

@app.get("/unofficial-devices/{device_id}/health-check/", response_model=DeviceHealthCheck)
def device_health_check(
    device_id: str,
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    try:
        return device_service.health_check(device_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@app.post("/unofficial-devices/cleanup-expired/")
def cleanup_expired_devices(
    device_service: UnofficialDeviceService = Depends(get_unofficial_device_service)
):
    count = device_service.cleanup_expired_devices()
    return {"cleaned_count": count, "message": f"Cleaned up {count} expired devices"}

# Message Usage & Credit Log endpoints
@app.post("/usage-logs/", response_model=UsageLogCreateResponse, status_code=status.HTTP_201_CREATED)
def create_usage_log(
    usage_request: UsageLogCreateRequest,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    try:
        return usage_service.create_usage_log(usage_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/usage-logs/", response_model=List[MessageUsageLogResponse])
def get_usage_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    device_id: Optional[str] = None,
    session_id: Optional[str] = None,
    message_id: Optional[str] = None,
    usage_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    # Build filter
    filters = UsageFilter(
        user_id=user_id,
        device_id=device_id,
        session_id=session_id,
        message_id=message_id,
        usage_type=UsageType(usage_type) if usage_type else None,
        status=UsageStatus(status) if status else None,
        start_date=start_date,
        end_date=end_date
    )
    
    usage_logs = usage_service.get_usage_logs(skip, limit, filters)
    return [
        MessageUsageLogResponse(
            usage_id=log.usage_id,
            user_id=log.user_id,
            message_id=log.message_id,
            device_id=log.device_id,
            session_id=log.session_id,
            usage_type=log.usage_type,
            credits_deducted=log.credits_deducted,
            credits_refunded=log.credits_refunded,
            net_credits=log.net_credits,
            balance_before=log.balance_before,
            balance_after=log.balance_after,
            cost_per_credit=float(log.cost_per_credit),
            total_cost=float(log.total_cost),
            currency=log.currency,
            message_type=log.message_type,
            message_size=log.message_size,
            recipient_count=log.recipient_count,
            delivery_status=log.delivery_status,
            status=log.status,
            error_code=log.error_code,
            error_message=log.error_message,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            api_endpoint=log.api_endpoint,
            request_id=log.request_id,
            refund_reason=log.refund_reason,
            refund_timestamp=log.refund_timestamp,
            refund_processed_by=log.refund_processed_by,
            created_at=log.created_at,
            updated_at=log.updated_at,
            processed_at=log.processed_at
        ) for log in usage_logs
    ]

@app.get("/usage-logs/{usage_id}", response_model=MessageUsageLogResponse)
def get_usage_log(
    usage_id: str,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    usage_log = usage_service.get_usage_log_by_id(usage_id)
    if not usage_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usage log not found"
        )
    
    return MessageUsageLogResponse(
        usage_id=usage_log.usage_id,
        user_id=usage_log.user_id,
        message_id=usage_log.message_id,
        device_id=usage_log.device_id,
        session_id=usage_log.session_id,
        usage_type=usage_log.usage_type,
        credits_deducted=usage_log.credits_deducted,
        credits_refunded=usage_log.credits_refunded,
        net_credits=usage_log.net_credits,
        balance_before=usage_log.balance_before,
        balance_after=usage_log.balance_after,
        cost_per_credit=float(usage_log.cost_per_credit),
        total_cost=float(usage_log.total_cost),
        currency=usage_log.currency,
        message_type=usage_log.message_type,
        message_size=usage_log.message_size,
        recipient_count=usage_log.recipient_count,
        delivery_status=usage_log.delivery_status,
        status=usage_log.status,
        error_code=usage_log.error_code,
        error_message=usage_log.error_message,
        ip_address=usage_log.ip_address,
        user_agent=usage_log.user_agent,
        api_endpoint=usage_log.api_endpoint,
        request_id=usage_log.request_id,
        refund_reason=usage_log.refund_reason,
        refund_timestamp=usage_log.refund_timestamp,
        refund_processed_by=usage_log.refund_processed_by,
        created_at=usage_log.created_at,
        updated_at=usage_log.updated_at,
        processed_at=usage_log.processed_at
    )

@app.get("/users/{user_id}/usage-logs/", response_model=List[MessageUsageLogResponse])
def get_user_usage_logs(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    usage_logs = usage_service.get_user_usage_logs(user_id, skip, limit)
    return [
        MessageUsageLogResponse(
            usage_id=log.usage_id,
            user_id=log.user_id,
            message_id=log.message_id,
            device_id=log.device_id,
            session_id=log.session_id,
            usage_type=log.usage_type,
            credits_deducted=log.credits_deducted,
            credits_refunded=log.credits_refunded,
            net_credits=log.net_credits,
            balance_before=log.balance_before,
            balance_after=log.balance_after,
            cost_per_credit=float(log.cost_per_credit),
            total_cost=float(log.total_cost),
            currency=log.currency,
            message_type=log.message_type,
            message_size=log.message_size,
            recipient_count=log.recipient_count,
            delivery_status=log.delivery_status,
            status=log.status,
            error_code=log.error_code,
            error_message=log.error_message,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            api_endpoint=log.api_endpoint,
            request_id=log.request_id,
            refund_reason=log.refund_reason,
            refund_timestamp=log.refund_timestamp,
            refund_processed_by=log.refund_processed_by,
            created_at=log.created_at,
            updated_at=log.updated_at,
            processed_at=log.processed_at
        ) for log in usage_logs
    ]

@app.get("/devices/{device_id}/usage-logs/", response_model=List[MessageUsageLogResponse])
def get_device_usage_logs(
    device_id: str,
    skip: int = 0,
    limit: int = 100,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    usage_logs = usage_service.get_device_usage_logs(device_id, skip, limit)
    return [
        MessageUsageLogResponse(
            usage_id=log.usage_id,
            user_id=log.user_id,
            message_id=log.message_id,
            device_id=log.device_id,
            session_id=log.session_id,
            usage_type=log.usage_type,
            credits_deducted=log.credits_deducted,
            credits_refunded=log.credits_refunded,
            net_credits=log.net_credits,
            balance_before=log.balance_before,
            balance_after=log.balance_after,
            cost_per_credit=float(log.cost_per_credit),
            total_cost=float(log.total_cost),
            currency=log.currency,
            message_type=log.message_type,
            message_size=log.message_size,
            recipient_count=log.recipient_count,
            delivery_status=log.delivery_status,
            status=log.status,
            error_code=log.error_code,
            error_message=log.error_message,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            api_endpoint=log.api_endpoint,
            request_id=log.request_id,
            refund_reason=log.refund_reason,
            refund_timestamp=log.refund_timestamp,
            refund_processed_by=log.refund_processed_by,
            created_at=log.created_at,
            updated_at=log.updated_at,
            processed_at=log.processed_at
        ) for log in usage_logs
    ]

@app.get("/sessions/{session_id}/usage-logs/", response_model=List[MessageUsageLogResponse])
def get_session_usage_logs(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    usage_logs = usage_service.get_session_usage_logs(session_id, skip, limit)
    return [
        MessageUsageLogResponse(
            usage_id=log.usage_id,
            user_id=log.user_id,
            message_id=log.message_id,
            device_id=log.device_id,
            session_id=log.session_id,
            usage_type=log.usage_type,
            credits_deducted=log.credits_deducted,
            credits_refunded=log.credits_refunded,
            net_credits=log.net_credits,
            balance_before=log.balance_before,
            balance_after=log.balance_after,
            cost_per_credit=float(log.cost_per_credit),
            total_cost=float(log.total_cost),
            currency=log.currency,
            message_type=log.message_type,
            message_size=log.message_size,
            recipient_count=log.recipient_count,
            delivery_status=log.delivery_status,
            status=log.status,
            error_code=log.error_code,
            error_message=log.error_message,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            api_endpoint=log.api_endpoint,
            request_id=log.request_id,
            refund_reason=log.refund_reason,
            refund_timestamp=log.refund_timestamp,
            refund_processed_by=log.refund_processed_by,
            created_at=log.created_at,
            updated_at=log.updated_at,
            processed_at=log.processed_at
        ) for log in usage_logs
    ]

@app.put("/usage-logs/{usage_id}", response_model=MessageUsageLogResponse)
def update_usage_log(
    usage_id: str,
    update_data: MessageUsageLogUpdate,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    usage_log = usage_service.update_usage_log(usage_id, update_data)
    if not usage_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usage log not found"
        )
    
    return MessageUsageLogResponse(
        usage_id=usage_log.usage_id,
        user_id=usage_log.user_id,
        message_id=usage_log.message_id,
        device_id=usage_log.device_id,
        session_id=usage_log.session_id,
        usage_type=usage_log.usage_type,
        credits_deducted=usage_log.credits_deducted,
        credits_refunded=usage_log.credits_refunded,
        net_credits=usage_log.net_credits,
        balance_before=usage_log.balance_before,
        balance_after=usage_log.balance_after,
        cost_per_credit=float(usage_log.cost_per_credit),
        total_cost=float(usage_log.total_cost),
        currency=usage_log.currency,
        message_type=usage_log.message_type,
        message_size=usage_log.message_size,
        recipient_count=usage_log.recipient_count,
        delivery_status=usage_log.delivery_status,
        status=usage_log.status,
        error_code=usage_log.error_code,
        error_message=usage_log.error_message,
        ip_address=usage_log.ip_address,
        user_agent=usage_log.user_agent,
        api_endpoint=usage_log.api_endpoint,
        request_id=usage_log.request_id,
        refund_reason=usage_log.refund_reason,
        refund_timestamp=usage_log.refund_timestamp,
        refund_processed_by=usage_log.refund_processed_by,
        created_at=usage_log.created_at,
        updated_at=usage_log.updated_at,
        processed_at=usage_log.processed_at
    )

@app.post("/usage-logs/refund/", response_model=UsageLogRefundResponse)
def refund_usage_log(
    refund_request: UsageLogRefundRequest,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    try:
        return usage_service.refund_usage_log(refund_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/usage-logs/mark-failed/", response_model=UsageLogUpdateResponse)
def mark_usage_failed(
    update_request: UsageLogUpdateRequest,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    try:
        return usage_service.mark_usage_failed(update_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/usage-logs/stats/", response_model=UsageStats)
def get_usage_stats(
    user_id: Optional[str] = None,
    device_id: Optional[str] = None,
    session_id: Optional[str] = None,
    usage_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    # Build filter
    filters = UsageFilter(
        user_id=user_id,
        device_id=device_id,
        session_id=session_id,
        usage_type=UsageType(usage_type) if usage_type else None,
        status=UsageStatus(status) if status else None,
        start_date=start_date,
        end_date=end_date
    )
    
    return usage_service.get_usage_stats(filters)

@app.get("/users/{user_id}/usage-stats/", response_model=UserUsageStats)
def get_user_usage_stats(
    user_id: str,
    days: int = 30,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    return usage_service.get_user_usage_stats(user_id, days)

@app.get("/devices/{device_id}/usage-stats/", response_model=DeviceUsageStats)
def get_device_usage_stats(
    device_id: str,
    days: int = 30,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    return usage_service.get_device_usage_stats(device_id, days)

@app.get("/sessions/{session_id}/usage-stats/", response_model=SessionUsageStats)
def get_session_usage_stats(
    session_id: str,
    usage_service: MessageUsageLogService = Depends(get_message_usage_log_service)
):
    return usage_service.get_session_usage_stats(session_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)