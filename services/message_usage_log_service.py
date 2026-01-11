from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from models.message_usage_log import MessageUsageLog, UsageType, UsageStatus
from models.user import User
from models.message import Message
from models.unofficial_device import UnofficialLinkedDevice
from models.device_session import DeviceSession
from schemas.message_usage_log import (
    MessageUsageLogCreate, MessageUsageLogUpdate, MessageUsageLogResponse,
    UsageLogCreateRequest, UsageLogCreateResponse, UsageLogRefundRequest, UsageLogRefundResponse,
    UsageLogUpdateRequest, UsageLogUpdateResponse, UsageStats, UserUsageStats,
    DeviceUsageStats, SessionUsageStats, UsageAnalytics, UsageFilter,
    BulkUsageOperation, BulkUsageResponse, UsageAuditLog, UsageHealthCheck,
    UsageCleanupRequest, UsageCleanupResponse
)
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class MessageUsageLogService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_usage_log(self, request: UsageLogCreateRequest) -> UsageLogCreateResponse:
        """Create a new usage log entry"""
        # Validate user exists
        user = self.db.query(User).filter(User.user_id == request.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Validate message exists if provided
        if request.message_id:
            message = self.db.query(Message).filter(Message.message_id == request.message_id).first()
            if not message:
                raise ValueError("Message not found")
        
        # Validate device exists if provided
        if request.device_id:
            device = self.db.query(UnofficialLinkedDevice).filter(
                UnofficialLinkedDevice.device_id == request.device_id
            ).first()
            if not device:
                raise ValueError("Device not found")
        
        # Validate session exists if provided
        if request.session_id:
            session = self.db.query(DeviceSession).filter(
                DeviceSession.session_id == request.session_id
            ).first()
            if not session:
                raise ValueError("Session not found")
        
        # Calculate balance after
        balance_after = request.balance_before - request.credits_deducted
        
        # Create usage log
        usage_log = MessageUsageLog.create_usage_log(
            user_id=request.user_id,
            message_id=request.message_id,
            device_id=request.device_id,
            session_id=request.session_id,
            usage_type=request.usage_type,
            credits_deducted=request.credits_deducted,
            balance_before=request.balance_before,
            balance_after=balance_after,
            cost_per_credit=0.01,  # Default cost per credit
            message_type=request.message_type,
            message_size=request.message_size,
            recipient_count=request.recipient_count,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            api_endpoint=request.api_endpoint,
            request_id=request.request_id
        )
        
        self.db.add(usage_log)
        self.db.commit()
        self.db.refresh(usage_log)
        
        return UsageLogCreateResponse(
            usage_id=usage_log.usage_id,
            user_id=usage_log.user_id,
            credits_deducted=usage_log.credits_deducted,
            balance_before=usage_log.balance_before,
            balance_after=usage_log.balance_after,
            total_cost=float(usage_log.total_cost),
            currency=usage_log.currency,
            status=usage_log.status,
            created_at=usage_log.created_at
        )
    
    def get_usage_log_by_id(self, usage_id: str) -> Optional[MessageUsageLog]:
        """Get usage log by ID"""
        return self.db.query(MessageUsageLog).filter(
            MessageUsageLog.usage_id == usage_id
        ).first()
    
    def get_usage_logs(self, skip: int = 0, limit: int = 100, filters: Optional[UsageFilter] = None) -> List[MessageUsageLog]:
        """Get usage logs with optional filters"""
        query = self.db.query(MessageUsageLog)
        
        if filters:
            if filters.user_id:
                query = query.filter(MessageUsageLog.user_id == filters.user_id)
            if filters.device_id:
                query = query.filter(MessageUsageLog.device_id == filters.device_id)
            if filters.session_id:
                query = query.filter(MessageUsageLog.session_id == filters.session_id)
            if filters.message_id:
                query = query.filter(MessageUsageLog.message_id == filters.message_id)
            if filters.usage_type:
                query = query.filter(MessageUsageLog.usage_type == filters.usage_type)
            if filters.status:
                query = query.filter(MessageUsageLog.status == filters.status)
            if filters.start_date:
                query = query.filter(MessageUsageLog.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(MessageUsageLog.created_at <= filters.end_date)
            if filters.min_credits:
                query = query.filter(MessageUsageLog.credits_deducted >= filters.min_credits)
            if filters.max_credits:
                query = query.filter(MessageUsageLog.credits_deducted <= filters.max_credits)
        
        return query.order_by(desc(MessageUsageLog.created_at)).offset(skip).limit(limit).all()
    
    def get_user_usage_logs(self, user_id: str, skip: int = 0, limit: int = 100) -> List[MessageUsageLog]:
        """Get usage logs for a specific user"""
        return self.db.query(MessageUsageLog).filter(
            MessageUsageLog.user_id == user_id
        ).order_by(desc(MessageUsageLog.created_at)).offset(skip).limit(limit).all()
    
    def get_device_usage_logs(self, device_id: str, skip: int = 0, limit: int = 100) -> List[MessageUsageLog]:
        """Get usage logs for a specific device"""
        return self.db.query(MessageUsageLog).filter(
            MessageUsageLog.device_id == device_id
        ).order_by(desc(MessageUsageLog.created_at)).offset(skip).limit(limit).all()
    
    def get_session_usage_logs(self, session_id: str, skip: int = 0, limit: int = 100) -> List[MessageUsageLog]:
        """Get usage logs for a specific session"""
        return self.db.query(MessageUsageLog).filter(
            MessageUsageLog.session_id == session_id
        ).order_by(desc(MessageUsageLog.created_at)).offset(skip).limit(limit).all()
    
    def update_usage_log(self, usage_id: str, update_data: MessageUsageLogUpdate) -> Optional[MessageUsageLog]:
        """Update usage log"""
        usage_log = self.get_usage_log_by_id(usage_id)
        if not usage_log:
            return None
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(usage_log, field, value)
        
        usage_log.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(usage_log)
        
        return usage_log
    
    def refund_usage_log(self, request: UsageLogRefundRequest) -> UsageLogRefundResponse:
        """Refund credits for a usage log"""
        usage_log = self.get_usage_log_by_id(request.usage_id)
        if not usage_log:
            raise ValueError("Usage log not found")
        
        try:
            usage_log.refund_credits(
                refund_amount=request.refund_amount,
                reason=request.refund_reason,
                processed_by=request.processed_by
            )
            
            self.db.commit()
            self.db.refresh(usage_log)
            
            return UsageLogRefundResponse(
                usage_id=usage_log.usage_id,
                credits_refunded=usage_log.credits_refunded,
                net_credits=usage_log.net_credits,
                refund_reason=usage_log.refund_reason,
                refund_timestamp=usage_log.refund_timestamp,
                message="Credits refunded successfully"
            )
            
        except ValueError as e:
            raise ValueError(str(e))
    
    def mark_usage_failed(self, request: UsageLogUpdateRequest) -> UsageLogUpdateResponse:
        """Mark usage as failed"""
        usage_log = self.get_usage_log_by_id(request.usage_id)
        if not usage_log:
            raise ValueError("Usage log not found")
        
        usage_log.mark_failed(
            error_code=request.error_code,
            error_message=request.error_message
        )
        
        if request.delivery_status:
            usage_log.delivery_status = request.delivery_status
        
        self.db.commit()
        self.db.refresh(usage_log)
        
        return UsageLogUpdateResponse(
            usage_id=usage_log.usage_id,
            status=usage_log.status,
            updated_at=usage_log.updated_at,
            message="Usage marked as failed"
        )
    
    def get_usage_stats(self, filters: Optional[UsageFilter] = None) -> UsageStats:
        """Get overall usage statistics"""
        query = self.db.query(MessageUsageLog)
        
        if filters:
            if filters.start_date:
                query = query.filter(MessageUsageLog.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(MessageUsageLog.created_at <= filters.end_date)
        
        # Total stats
        total_usage = query.count()
        total_credits_deducted = query.with_entities(func.sum(MessageUsageLog.credits_deducted)).scalar() or 0
        total_credits_refunded = query.with_entities(func.sum(MessageUsageLog.credits_refunded)).scalar() or 0
        net_credits_used = total_credits_deducted - total_credits_refunded
        total_cost = query.with_entities(func.sum(MessageUsageLog.total_cost)).scalar() or Decimal('0.00')
        
        # Status breakdown
        successful_usage = query.filter(MessageUsageLog.status == UsageStatus.SUCCESS).count()
        failed_usage = query.filter(MessageUsageLog.status == UsageStatus.FAILED).count()
        refunded_usage = query.filter(MessageUsageLog.status == UsageStatus.REFUNDED).count()
        
        # Usage by type
        usage_by_type = {}
        for usage_type in UsageType:
            count = query.filter(MessageUsageLog.usage_type == usage_type).count()
            if count > 0:
                usage_by_type[usage_type.value] = count
        
        # Usage by status
        usage_by_status = {}
        for status in UsageStatus:
            count = query.filter(MessageUsageLog.status == status).count()
            if count > 0:
                usage_by_status[status.value] = count
        
        average_cost_per_usage = float(total_cost) / total_usage if total_usage > 0 else 0.0
        
        return UsageStats(
            total_usage=total_usage,
            total_credits_deducted=total_credits_deducted,
            total_credits_refunded=total_credits_refunded,
            net_credits_used=net_credits_used,
            total_cost=float(total_cost),
            successful_usage=successful_usage,
            failed_usage=failed_usage,
            refunded_usage=refunded_usage,
            average_cost_per_usage=average_cost_per_usage,
            usage_by_type=usage_by_type,
            usage_by_status=usage_by_status
        )
    
    def get_user_usage_stats(self, user_id: str, days: int = 30) -> UserUsageStats:
        """Get usage statistics for a specific user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        user_usage = self.db.query(MessageUsageLog).filter(
            and_(
                MessageUsageLog.user_id == user_id,
                MessageUsageLog.created_at >= start_date
            )
        )
        
        # Get current user balance
        user = self.db.query(User).filter(User.user_id == user_id).first()
        current_balance = user.available_credits if user else 0
        
        # Total stats
        total_usage = user_usage.count()
        total_credits_deducted = user_usage.with_entities(func.sum(MessageUsageLog.credits_deducted)).scalar() or 0
        total_credits_refunded = user_usage.with_entities(func.sum(MessageUsageLog.credits_refunded)).scalar() or 0
        net_credits_used = total_credits_deducted - total_credits_refunded
        total_cost = user_usage.with_entities(func.sum(MessageUsageLog.total_cost)).scalar() or Decimal('0.00')
        
        # Usage by type
        usage_by_type = {}
        for usage_type in UsageType:
            count = user_usage.filter(MessageUsageLog.usage_type == usage_type).count()
            if count > 0:
                usage_by_type[usage_type.value] = count
        
        # Usage by status
        usage_by_status = {}
        for status in UsageStatus:
            count = user_usage.filter(MessageUsageLog.status == status).count()
            if count > 0:
                usage_by_status[status.value] = count
        
        # Daily usage
        daily_usage = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_end = day + timedelta(days=1)
            day_count = user_usage.filter(
                and_(
                    MessageUsageLog.created_at >= day,
                    MessageUsageLog.created_at < day_end
                )
            ).count()
            daily_usage.append({
                "date": day.date().isoformat(),
                "usage_count": day_count
            })
        
        # Hourly usage (last 24 hours)
        hourly_usage = []
        for i in range(24):
            hour = datetime.utcnow() - timedelta(hours=i)
            hour_end = hour + timedelta(hours=1)
            hour_count = user_usage.filter(
                and_(
                    MessageUsageLog.created_at >= hour,
                    MessageUsageLog.created_at < hour_end
                )
            ).count()
            hourly_usage.append({
                "hour": hour.strftime("%H:00"),
                "usage_count": hour_count
            })
        
        return UserUsageStats(
            user_id=user_id,
            total_usage=total_usage,
            total_credits_deducted=total_credits_deducted,
            total_credits_refunded=total_credits_refunded,
            net_credits_used=net_credits_used,
            total_cost=float(total_cost),
            current_balance=current_balance,
            usage_by_type=usage_by_type,
            usage_by_status=usage_by_status,
            daily_usage=daily_usage,
            hourly_usage=hourly_usage
        )
    
    def get_device_usage_stats(self, device_id: str, days: int = 30) -> DeviceUsageStats:
        """Get usage statistics for a specific device"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        device_usage = self.db.query(MessageUsageLog).filter(
            and_(
                MessageUsageLog.device_id == device_id,
                MessageUsageLog.created_at >= start_date
            )
        )
        
        # Get device name
        device = self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.device_id == device_id
        ).first()
        device_name = device.device_name if device else None
        
        # Total stats
        total_usage = device_usage.count()
        total_credits_deducted = device_usage.with_entities(func.sum(MessageUsageLog.credits_deducted)).scalar() or 0
        total_credits_refunded = device_usage.with_entities(func.sum(MessageUsageLog.credits_refunded)).scalar() or 0
        net_credits_used = total_credits_deducted - total_credits_refunded
        total_cost = device_usage.with_entities(func.sum(MessageUsageLog.total_cost)).scalar() or Decimal('0.00')
        
        # Usage by type and status
        usage_by_type = {}
        for usage_type in UsageType:
            count = device_usage.filter(MessageUsageLog.usage_type == usage_type).count()
            if count > 0:
                usage_by_type[usage_type.value] = count
        
        usage_by_status = {}
        for status in UsageStatus:
            count = device_usage.filter(MessageUsageLog.status == status).count()
            if count > 0:
                usage_by_status[status.value] = count
        
        # Daily usage
        daily_usage = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_end = day + timedelta(days=1)
            day_count = device_usage.filter(
                and_(
                    MessageUsageLog.created_at >= day,
                    MessageUsageLog.created_at < day_end
                )
            ).count()
            daily_usage.append({
                "date": day.date().isoformat(),
                "usage_count": day_count
            })
        
        return DeviceUsageStats(
            device_id=device_id,
            device_name=device_name,
            total_usage=total_usage,
            total_credits_deducted=total_credits_deducted,
            total_credits_refunded=total_credits_refunded,
            net_credits_used=net_credits_used,
            total_cost=float(total_cost),
            usage_by_type=usage_by_type,
            usage_by_status=usage_by_status,
            daily_usage=daily_usage
        )
    
    def get_session_usage_stats(self, session_id: str) -> SessionUsageStats:
        """Get usage statistics for a specific session"""
        session_usage = self.db.query(MessageUsageLog).filter(
            MessageUsageLog.session_id == session_id
        )
        
        # Get session duration
        session = self.db.query(DeviceSession).filter(
            DeviceSession.session_id == session_id
        ).first()
        
        session_duration_minutes = None
        if session:
            if session.expires_at:
                duration = session.expires_at - session.created_at
                session_duration_minutes = duration.total_seconds() / 60
        
        # Total stats
        total_usage = session_usage.count()
        total_credits_deducted = session_usage.with_entities(func.sum(MessageUsageLog.credits_deducted)).scalar() or 0
        total_credits_refunded = session_usage.with_entities(func.sum(MessageUsageLog.credits_refunded)).scalar() or 0
        net_credits_used = total_credits_deducted - total_credits_refunded
        total_cost = session_usage.with_entities(func.sum(MessageUsageLog.total_cost)).scalar() or Decimal('0.00')
        
        # Usage by type and status
        usage_by_type = {}
        for usage_type in UsageType:
            count = session_usage.filter(MessageUsageLog.usage_type == usage_type).count()
            if count > 0:
                usage_by_type[usage_type.value] = count
        
        usage_by_status = {}
        for status in UsageStatus:
            count = session_usage.filter(MessageUsageLog.status == status).count()
            if count > 0:
                usage_by_status[status.value] = count
        
        return SessionUsageStats(
            session_id=session_id,
            total_usage=total_usage,
            total_credits_deducted=total_credits_deducted,
            total_credits_refunded=total_credits_refunded,
            net_credits_used=net_credits_used,
            total_cost=float(total_cost),
            usage_by_type=usage_by_type,
            usage_by_status=usage_by_status,
            session_duration_minutes=session_duration_minutes
        )
    
    def bulk_usage_operation(self, operation: BulkUsageOperation) -> BulkUsageResponse:
        """Perform bulk operations on usage logs"""
        successful = 0
        failed = 0
        errors = []
        
        for usage_id in operation.usage_ids:
            try:
                usage_log = self.get_usage_log_by_id(usage_id)
                if not usage_log:
                    errors.append({"usage_id": usage_id, "error": "Usage log not found"})
                    failed += 1
                    continue
                
                if operation.operation == "refund":
                    if operation.refund_amount and operation.refund_reason:
                        usage_log.refund_credits(
                            refund_amount=operation.refund_amount,
                            reason=operation.refund_reason,
                            processed_by=operation.processed_by
                        )
                        successful += 1
                    else:
                        errors.append({"usage_id": usage_id, "error": "Refund amount and reason required"})
                        failed += 1
                
                elif operation.operation == "update":
                    if operation.new_status:
                        usage_log.status = operation.new_status
                        usage_log.updated_at = datetime.utcnow()
                        successful += 1
                    else:
                        errors.append({"usage_id": usage_id, "error": "New status required"})
                        failed += 1
                
                elif operation.operation == "delete":
                    self.db.delete(usage_log)
                    successful += 1
                
            except Exception as e:
                errors.append({"usage_id": usage_id, "error": str(e)})
                failed += 1
        
        if successful > 0:
            self.db.commit()
        
        return BulkUsageResponse(
            operation=operation.operation,
            total_processed=len(operation.usage_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            message=f"Bulk {operation.operation} completed"
        )
    
    def cleanup_old_usage_logs(self, cleanup_request: UsageCleanupRequest) -> UsageCleanupResponse:
        """Clean up old usage logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=cleanup_request.older_than_days)
        
        query = self.db.query(MessageUsageLog).filter(
            MessageUsageLog.created_at < cutoff_date
        )
        
        if cleanup_request.status_filter:
            query = query.filter(MessageUsageLog.status.in_(cleanup_request.status_filter))
        
        total_records_found = query.count()
        
        if cleanup_request.dry_run:
            return UsageCleanupResponse(
                total_records_found=total_records_found,
                records_to_delete=total_records_found,
                records_deleted=0,
                dry_run=True,
                message=f"Found {total_records_found} records to delete (dry run)"
            )
        
        # Actually delete the records
        deleted_count = query.delete()
        self.db.commit()
        
        return UsageCleanupResponse(
            total_records_found=total_records_found,
            records_to_delete=total_records_found,
            records_deleted=deleted_count,
            dry_run=False,
            message=f"Deleted {deleted_count} old usage logs"
        )
