from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime, timedelta
import uuid
import secrets
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DeviceSession(Base):
    __tablename__ = "device_sessions"
    
    session_id = Column(String, primary_key=True, default=lambda: f"session-{uuid.uuid4().hex[:8]}")
    device_id = Column(String, ForeignKey("unofficial_linked_devices.device_id"), nullable=False, index=True)
    
    # Authentication data
    session_token = Column(Text, nullable=False)  # Encrypted session data
    encryption_key = Column(String, nullable=False)  # Key for decrypting session data
    salt = Column(String, nullable=False)  # Salt for key derivation
    
    # Session status
    is_valid = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    session_type = Column(String, default="unofficial")  # unofficial, official
    
    # Session metadata
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    last_ip_address = Column(String, nullable=True)
    
    # Security tracking
    login_attempts = Column(Integer, default=0)
    max_login_attempts = Column(Integer, default=5)
    last_login_attempt = Column(DateTime, nullable=True)
    last_successful_login = Column(DateTime, nullable=True)
    
    # Activity tracking
    last_activity = Column(DateTime, default=datetime.utcnow)
    total_requests = Column(Integer, default=0)
    messages_sent_via_session = Column(Integer, default=0)
    
    # Session lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_extended_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Security flags
    is_compromised = Column(Boolean, default=False)
    compromise_reason = Column(Text, nullable=True)
    requires_reauth = Column(Boolean, default=False)
    
    # Relationships
    device = relationship("UnofficialLinkedDevice", back_populates="sessions")
    usage_logs = relationship("MessageUsageLog", back_populates="session")
    
    def __repr__(self):
        return f"<DeviceSession(id={self.session_id}, device_id={self.device_id}, valid={self.is_valid})>"
    
    def is_expired(self):
        """Check if session has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid_session(self):
        """Check if session is both valid and not expired"""
        return self.is_valid and self.is_active and not self.is_expired() and not self.is_compromised
    
    def can_login(self):
        """Check if user can attempt login"""
        return self.login_attempts < self.max_login_attempts
    
    def increment_login_attempt(self):
        """Increment failed login attempts"""
        self.login_attempts += 1
        self.last_login_attempt = datetime.utcnow()
        
        # Lock account if max attempts reached
        if self.login_attempts >= self.max_login_attempts:
            self.is_valid = False
            self.requires_reauth = True
    
    def successful_login(self):
        """Reset login attempts on successful login"""
        self.login_attempts = 0
        self.last_successful_login = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_valid = True
        self.requires_reauth = False
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_extended_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
    
    def revoke_session(self, reason: str = None):
        """Revoke the session"""
        self.is_valid = False
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        if reason:
            self.compromise_reason = reason
    
    def mark_compromised(self, reason: str):
        """Mark session as compromised"""
        self.is_compromised = True
        self.is_valid = False
        self.is_active = False
        self.compromise_reason = reason
        self.revoked_at = datetime.utcnow()
    
    def update_activity(self, ip_address: str = None):
        """Update session activity"""
        self.last_activity = datetime.utcnow()
        self.total_requests += 1
        if ip_address:
            self.last_ip_address = ip_address
    
    def increment_message_count(self):
        """Increment message count for this session"""
        self.messages_sent_via_session += 1
        self.last_activity = datetime.utcnow()
    
    @staticmethod
    def generate_encryption_key(password: str, salt: str = None) -> tuple:
        """Generate encryption key from password"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_session_data(data: str, password: str) -> tuple:
        """Encrypt session data"""
        key, salt = DeviceSession.generate_encryption_key(password)
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return encrypted_data.decode(), key.decode(), salt
    
    @staticmethod
    def decrypt_session_data(encrypted_data: str, key: str) -> str:
        """Decrypt session data"""
        f = Fernet(key.encode())
        decrypted_data = f.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(64)
    
    def get_session_info(self) -> dict:
        """Get session information (excluding sensitive data)"""
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "is_valid": self.is_valid,
            "is_active": self.is_active,
            "session_type": self.session_type,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_activity": self.last_activity,
            "total_requests": self.total_requests,
            "messages_sent_via_session": self.messages_sent_via_session,
            "is_expired": self.is_expired(),
            "is_compromised": self.is_compromised,
            "requires_reauth": self.requires_reauth
        }
