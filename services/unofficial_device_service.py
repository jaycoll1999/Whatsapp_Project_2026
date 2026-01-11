from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.unofficial_device import UnofficialLinkedDevice
from models.user import User
from schemas.unofficial_device import (
    UnofficialDeviceCreate, UnofficialDeviceUpdate, UnofficialDeviceResponse,
    QRCodeRequest, QRCodeResponse, DeviceConnectRequest, DeviceConnectResponse,
    DeviceDisconnectRequest, DeviceDisconnectResponse, DeviceStatusUpdate,
    DeviceStats, UserDeviceStats, DeviceActivityLog, BulkDeviceOperation,
    DeviceHealthCheck, DeviceMaintenanceRequest
)
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import base64
import qrcode
import io

class UnofficialDeviceService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_device(self, device_data: UnofficialDeviceCreate) -> UnofficialLinkedDevice:
        # Validate user exists
        user = self.db.query(User).filter(User.user_id == device_data.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if user has reached device limit (max 5 devices per user)
        device_count = self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.user_id == device_data.user_id,
            UnofficialLinkedDevice.is_active == True
        ).count()
        
        if device_count >= 5:
            raise ValueError("Maximum device limit reached (5 devices per user)")
        
        # Create device
        device = UnofficialLinkedDevice(
            user_id=device_data.user_id,
            device_name=device_data.device_name,
            device_type=device_data.device_type.value,
            device_os=device_data.device_os,
            browser_info=device_data.browser_info,
            ip_address=device_data.ip_address,
            max_daily_messages=device_data.max_daily_messages,
            session_status="disconnected"
        )
        
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    def get_device_by_id(self, device_id: str) -> Optional[UnofficialLinkedDevice]:
        return self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.device_id == device_id
        ).first()
    
    def get_devices_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[UnofficialLinkedDevice]:
        return self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_all_devices(self, skip: int = 0, limit: int = 100) -> List[UnofficialLinkedDevice]:
        return self.db.query(UnofficialLinkedDevice).offset(skip).limit(limit).all()
    
    def update_device(self, device_id: str, update_data: UnofficialDeviceUpdate) -> Optional[UnofficialLinkedDevice]:
        device = self.get_device_by_id(device_id)
        if not device:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(device, field, value)
        
        device.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    def delete_device(self, device_id: str) -> bool:
        device = self.get_device_by_id(device_id)
        if not device:
            return False
        
        # Soft delete
        device.is_active = False
        device.session_status = "disconnected"
        device.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def generate_qr_code(self, device_id: str, regenerate: bool = False) -> QRCodeResponse:
        device = self.get_device_by_id(device_id)
        if not device:
            raise ValueError("Device not found")
        
        # Check if existing QR code is still valid
        if not regenerate and device.qr_code_data and not device.is_expired():
            return QRCodeResponse(
                device_id=device.device_id,
                qr_code_data=device.qr_code_data,
                qr_last_generated=device.qr_last_generated,
                qr_expires_at=device.qr_expires_at,
                session_status=device.session_status
            )
        
        # Generate new QR code
        qr_data = f"wa-device-{device.device_id}-{uuid.uuid4().hex[:16]}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Update device
        device.qr_code_data = qr_base64
        device.qr_last_generated = datetime.utcnow()
        device.qr_expires_at = datetime.utcnow() + timedelta(minutes=5)  # QR expires in 5 minutes
        device.session_status = "pending"
        device.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return QRCodeResponse(
            device_id=device.device_id,
            qr_code_data=qr_base64,
            qr_last_generated=device.qr_last_generated,
            qr_expires_at=device.qr_expires_at,
            session_status=device.session_status
        )
    
    def connect_device(self, connect_request: DeviceConnectRequest) -> DeviceConnectResponse:
        device = self.get_device_by_id(connect_request.device_id)
        if not device:
            raise ValueError("Device not found")
        
        if device.session_status == "connected":
            return DeviceConnectResponse(
                device_id=device.device_id,
                session_status=device.session_status,
                connected_at=datetime.utcnow(),
                connection_successful=False,
                message="Device is already connected"
            )
        
        if device.is_expired():
            return DeviceConnectResponse(
                device_id=device.device_id,
                session_status=device.session_status,
                connected_at=datetime.utcnow(),
                connection_successful=False,
                message="QR code has expired. Please generate a new QR code."
            )
        
        # Simulate connection (in real implementation, this would connect to WhatsApp)
        device.session_status = "connected"
        device.connection_string = connect_request.connection_string
        device.last_connected_at = datetime.utcnow()
        device.last_active = datetime.utcnow()
        device.error_count = 0
        device.reconnect_attempts = 0
        device.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return DeviceConnectResponse(
            device_id=device.device_id,
            session_status=device.session_status,
            connected_at=device.last_connected_at,
            connection_successful=True,
            message="Device connected successfully"
        )
    
    def disconnect_device(self, disconnect_request: DeviceDisconnectRequest) -> DeviceDisconnectResponse:
        device = self.get_device_by_id(disconnect_request.device_id)
        if not device:
            raise ValueError("Device not found")
        
        device.session_status = "disconnected"
        device.last_disconnected_at = datetime.utcnow()
        device.connection_string = None
        device.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return DeviceDisconnectResponse(
            device_id=device.device_id,
            session_status=device.session_status,
            disconnected_at=device.last_disconnected_at,
            message="Device disconnected successfully"
        )
    
    def update_device_status(self, status_update: DeviceStatusUpdate) -> UnofficialLinkedDevice:
        device = self.get_device_by_id(status_update.device_id)
        if not device:
            raise ValueError("Device not found")
        
        device.session_status = status_update.session_status
        device.last_active = datetime.utcnow()
        
        if status_update.last_error:
            device.last_error = status_update.last_error
            device.error_count += 1
        
        if status_update.ip_address:
            device.ip_address = status_update.ip_address
        
        device.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(device)
        
        return device
    
    def get_device_stats(self, device_id: str) -> DeviceStats:
        device = self.get_device_by_id(device_id)
        if not device:
            raise ValueError("Device not found")
        
        # Calculate uptime percentage (simplified)
        uptime_percentage = 0.0
        if device.created_at:
            total_time = (datetime.utcnow() - device.created_at).total_seconds() / 60  # in minutes
            if total_time > 0:
                uptime_percentage = (device.total_activity_time / total_time) * 100
        
        return DeviceStats(
            device_id=device.device_id,
            device_name=device.device_name,
            session_status=device.session_status,
            messages_sent=device.messages_sent,
            messages_received=device.messages_received,
            daily_message_count=device.daily_message_count,
            max_daily_messages=device.max_daily_messages,
            total_activity_time=device.total_activity_time,
            last_active=device.last_active,
            uptime_percentage=min(uptime_percentage, 100.0)
        )
    
    def get_user_device_stats(self, user_id: str) -> UserDeviceStats:
        devices = self.get_devices_by_user(user_id)
        
        total_devices = len(devices)
        active_devices = len([d for d in devices if d.is_active])
        connected_devices = len([d for d in devices if d.session_status == "connected"])
        
        total_messages_sent = sum(d.messages_sent for d in devices)
        total_messages_received = sum(d.messages_received for d in devices)
        
        device_stats = []
        for device in devices:
            stats = self.get_device_stats(device.device_id)
            device_stats.append(stats)
        
        return UserDeviceStats(
            user_id=user_id,
            total_devices=total_devices,
            active_devices=active_devices,
            connected_devices=connected_devices,
            total_messages_sent=total_messages_sent,
            total_messages_received=total_messages_received,
            devices=device_stats
        )
    
    def bulk_device_operation(self, operation: BulkDeviceOperation) -> dict:
        results = {"success": 0, "failed": 0, "details": []}
        
        for device_id in operation.device_ids:
            try:
                device = self.get_device_by_id(device_id)
                if not device:
                    results["failed"] += 1
                    results["details"].append(f"Device {device_id} not found")
                    continue
                
                if operation.operation == "disconnect":
                    device.session_status = "disconnected"
                    device.last_disconnected_at = datetime.utcnow()
                elif operation.operation == "reconnect":
                    device.session_status = "connected"
                    device.last_connected_at = datetime.utcnow()
                    device.reconnect_attempts = 0
                elif operation.operation == "reset_daily_count":
                    device.daily_message_count = 0
                    device.last_reset_date = datetime.utcnow()
                elif operation.operation == "activate":
                    device.is_active = True
                elif operation.operation == "deactivate":
                    device.is_active = False
                    device.session_status = "disconnected"
                
                device.updated_at = datetime.utcnow()
                self.db.commit()
                results["success"] += 1
                results["details"].append(f"Device {device_id} {operation.operation} successful")
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"Device {device_id} failed: {str(e)}")
        
        return results
    
    def health_check(self, device_id: str) -> DeviceHealthCheck:
        device = self.get_device_by_id(device_id)
        if not device:
            raise ValueError("Device not found")
        
        start_time = datetime.utcnow()
        issues = []
        
        # Check if device is responsive
        is_responsive = device.session_status == "connected" and device.is_active
        
        # Check for common issues
        if device.session_status == "disconnected":
            issues.append("Device is disconnected")
        
        if device.error_count > 5:
            issues.append("High error count detected")
        
        if device.daily_message_count >= device.max_daily_messages:
            issues.append("Daily message limit reached")
        
        if device.is_expired():
            issues.append("QR code expired")
        
        # Calculate response time (mock)
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return DeviceHealthCheck(
            device_id=device.device_id,
            is_responsive=is_responsive,
            response_time_ms=response_time_ms,
            last_check=datetime.utcnow(),
            issues=issues
        )
    
    def cleanup_expired_devices(self) -> int:
        """Clean up devices with expired QR codes or long inactivity"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        expired_devices = self.db.query(UnofficialLinkedDevice).filter(
            or_(
                and_(
                    UnofficialLinkedDevice.qr_expires_at < datetime.utcnow(),
                    UnofficialLinkedDevice.session_status == "pending"
                ),
                UnofficialLinkedDevice.last_active < cutoff_time
            )
        ).all()
        
        count = 0
        for device in expired_devices:
            if device.session_status == "pending":
                device.session_status = "expired"
                device.qr_code_data = None
            elif device.last_active < cutoff_time and device.session_status != "connected":
                device.is_active = False
                device.session_status = "disconnected"
            
            device.updated_at = datetime.utcnow()
            count += 1
        
        self.db.commit()
        return count
    
    def reset_daily_message_counts(self) -> int:
        """Reset daily message counts for all devices"""
        today = datetime.utcnow().date()
        
        devices_to_reset = self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.last_reset_date < today
        ).all()
        
        for device in devices_to_reset:
            device.daily_message_count = 0
            device.last_reset_date = datetime.utcnow()
        
        self.db.commit()
        return len(devices_to_reset)
