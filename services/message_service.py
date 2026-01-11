from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.message import Message
from models.user import User
from schemas.message import MessageCreate, MessageUpdate, MessageSendRequest, BulkMessageRequest, MessageStats
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import requests

class MessageService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(self, message_data: MessageCreate) -> Message:
        # Validate user exists and has sufficient credits
        user = self.db.query(User).filter(User.user_id == message_data.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.role == "business_owner":
            if user.credits_remaining < message_data.credits_used:
                raise ValueError("Insufficient credits")
            # Deduct credits for business owner
            user.credits_used += message_data.credits_used
            user.credits_remaining -= message_data.credits_used
        elif user.role == "reseller":
            if user.available_credits < message_data.credits_used:
                raise ValueError("Insufficient credits")
            # Deduct credits for reseller
            user.used_credits += message_data.credits_used
            user.available_credits -= message_data.credits_used
        
        # Create message
        message = Message(
            user_id=message_data.user_id,
            channel=message_data.channel.value,
            mode=message_data.mode.value,
            sender_number=message_data.sender_number,
            receiver_number=message_data.receiver_number,
            message_type=message_data.message_type.value,
            template_name=message_data.template_name,
            message_body=message_data.message_body,
            credits_used=message_data.credits_used,
            status="pending"
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # Send message (async or sync based on mode)
        self._send_message(message)
        
        return message
    
    def send_message(self, user_id: str, message_request: MessageSendRequest) -> Message:
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        message_data = MessageCreate(
            user_id=user_id,
            channel="whatsapp",
            mode=message_request.mode,
            sender_number=user.phone,
            receiver_number=message_request.receiver_number,
            message_type=message_request.message_type,
            template_name=message_request.template_name,
            message_body=message_request.message_body,
            credits_used=1
        )
        
        return self.create_message(message_data)
    
    def send_bulk_messages(self, user_id: str, bulk_request: BulkMessageRequest) -> List[Message]:
        messages = []
        for receiver_number in bulk_request.receiver_numbers:
            try:
                message = self.send_message(
                    user_id=user_id,
                    message_request=MessageSendRequest(
                        receiver_number=receiver_number,
                        message_type=bulk_request.message_type,
                        template_name=bulk_request.template_name,
                        message_body=bulk_request.message_body,
                        mode=bulk_request.mode
                    )
                )
                messages.append(message)
            except Exception as e:
                # Log error but continue with other messages
                print(f"Failed to send message to {receiver_number}: {e}")
        
        return messages
    
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        return self.db.query(Message).filter(Message.message_id == message_id).first()
    
    def get_messages_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Message]:
        return self.db.query(Message).filter(Message.user_id == user_id).offset(skip).limit(limit).all()
    
    def get_messages_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Message]:
        return self.db.query(Message).filter(Message.status == status).offset(skip).limit(limit).all()
    
    def get_all_messages(self, skip: int = 0, limit: int = 100) -> List[Message]:
        return self.db.query(Message).offset(skip).limit(limit).all()
    
    def update_message_status(self, message_id: str, update_data: MessageUpdate) -> Optional[Message]:
        message = self.get_message_by_id(message_id)
        if not message:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(message, field, value)
        
        message.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def retry_failed_messages(self, max_retries: int = 3) -> List[Message]:
        failed_messages = self.db.query(Message).filter(
            and_(
                Message.status == "failed",
                Message.retry_count < max_retries
            )
        ).all()
        
        retried_messages = []
        for message in failed_messages:
            message.retry_count += 1
            message.status = "pending"
            message.error_message = None
            
            try:
                self._send_message(message)
                retried_messages.append(message)
            except Exception as e:
                message.error_message = str(e)
                message.status = "failed"
            
            self.db.commit()
        
        return retried_messages
    
    def get_message_stats(self, user_id: Optional[str] = None) -> MessageStats:
        query = self.db.query(Message)
        if user_id:
            query = query.filter(Message.user_id == user_id)
        
        total_messages = query.count()
        messages_sent = query.filter(Message.status == "sent").count()
        messages_delivered = query.filter(Message.status == "delivered").count()
        messages_failed = query.filter(Message.status == "failed").count()
        messages_read = query.filter(Message.status == "read").count()
        
        total_credits_used = query.with_entities(func.sum(Message.credits_used)).scalar() or 0
        
        # Calculate average delivery time
        delivery_times = []
        delivered_messages = query.filter(
            and_(
                Message.status == "delivered",
                Message.delivered_at.isnot(None),
                Message.sent_at.isnot(None)
            )
        ).all()
        
        for msg in delivered_messages:
            delivery_time = (msg.delivered_at - msg.sent_at).total_seconds()
            delivery_times.append(delivery_time)
        
        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else None
        
        return MessageStats(
            total_messages=total_messages,
            messages_sent=messages_sent,
            messages_delivered=messages_delivered,
            messages_failed=messages_failed,
            messages_read=messages_read,
            total_credits_used=total_credits_used,
            average_delivery_time=avg_delivery_time
        )
    
    def _send_message(self, message: Message):
        """Internal method to send message via appropriate channel"""
        try:
            if message.mode == "official":
                # Use official WhatsApp API
                response = self._send_via_official_api(message)
            else:
                # Use unofficial WhatsApp method
                response = self._send_via_unofficial_method(message)
            
            # Update message status based on response
            if response.get("success", False):
                message.status = "sent"
                message.external_message_id = response.get("message_id")
                message.webhook_response = str(response)
            else:
                message.status = "failed"
                message.error_message = response.get("error", "Unknown error")
            
            message.sent_at = datetime.utcnow()
            
        except Exception as e:
            message.status = "failed"
            message.error_message = str(e)
            message.sent_at = datetime.utcnow()
        
        self.db.commit()
    
    def _send_via_official_api(self, message: Message) -> dict:
        """Send message via official WhatsApp API"""
        # This would integrate with actual WhatsApp Business API
        # For now, return mock response
        return {
            "success": True,
            "message_id": f"wa-official-{uuid.uuid4().hex[:12]}",
            "status": "sent"
        }
    
    def _send_via_unofficial_method(self, message: Message) -> dict:
        """Send message via unofficial WhatsApp method"""
        # This would integrate with libraries like whatsapp-web.js
        # For now, return mock response
        return {
            "success": True,
            "message_id": f"wa-unofficial-{uuid.uuid4().hex[:12]}",
            "status": "sent"
        }
    
    def process_webhook(self, message_id: str, webhook_data: dict) -> Optional[Message]:
        """Process webhook updates from WhatsApp"""
        message = self.get_message_by_id(message_id)
        if not message:
            return None
        
        # Update message based on webhook data
        if webhook_data.get("status") == "delivered":
            message.status = "delivered"
            message.delivered_at = datetime.utcnow()
        elif webhook_data.get("status") == "read":
            message.status = "read"
            message.read_at = datetime.utcnow()
        elif webhook_data.get("status") == "failed":
            message.status = "failed"
            message.error_message = webhook_data.get("error")
        
        message.webhook_response = str(webhook_data)
        self.db.commit()
        self.db.refresh(message)
        
        return message
