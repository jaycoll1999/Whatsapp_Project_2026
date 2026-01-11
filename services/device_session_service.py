from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.device_session import DeviceSession
from models.unofficial_device import UnofficialLinkedDevice
from schemas.device_session import (
    DeviceSessionCreate, DeviceSessionUpdate, DeviceSessionResponse,
    SessionCreateRequest, SessionCreateResponse, SessionValidateRequest, SessionValidateResponse,
    SessionExtendRequest, SessionExtendResponse, SessionRevokeRequest, SessionRevokeResponse,
    SessionLoginRequest, SessionLoginResponse, SessionActivityUpdate,
    SessionStats, DeviceSessionStats, UserSessionStats, SessionSecurityCheck,
    BulkSessionOperation, SessionCleanupRequest, SessionCleanupResponse,
    SessionAuditLog, SessionHealthCheck
)
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)

class DeviceSessionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session_request: SessionCreateRequest) -> SessionCreateResponse:
        # Validate device exists
        device = self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.device_id == session_request.device_id
        ).first()
        if not device:
            raise ValueError("Device not found")
        
        # Check if device is connected
        if device.session_status != "connected":
            raise ValueError("Device must be connected to create a session")
        
        # Check for existing active sessions
        existing_sessions = self.db.query(DeviceSession).filter(
            and_(
                DeviceSession.device_id == session_request.device_id,
                DeviceSession.is_valid == True,
                DeviceSession.is_active == True,
                DeviceSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        # Allow max 3 active sessions per device
        if existing_sessions >= 3:
            # Revoke oldest session
            oldest_session = self.db.query(DeviceSession).filter(
                and_(
                    DeviceSession.device_id == session_request.device_id,
                    DeviceSession.is_valid == True,
                    DeviceSession.is_active == True
                )
            ).order_by(DeviceSession.created_at).first()
            
            if oldest_session:
                oldest_session.revoke_session("Max sessions reached, creating new session")
        
        # Encrypt session data
        session_password = secrets.token_urlsafe(32)
        encrypted_data, key, salt = DeviceSession.encrypt_session_data(
            session_request.session_data, 
            session_password
        )
        
        # Create session
        expires_at = datetime.utcnow() + timedelta(hours=session_request.expires_in_hours)
        
        session = DeviceSession(
            device_id=session_request.device_id,
            session_token=encrypted_data,
            encryption_key=key,
            salt=salt,
            session_type="unofficial",
            user_agent=session_request.user_agent,
            ip_address=session_request.ip_address,
            max_login_attempts=5,
            expires_at=expires_at
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return SessionCreateResponse(
            session_id=session.session_id,
            device_id=session.device_id,
            session_token=encrypted_data,
            expires_at=session.expires_at,
            created_at=session.created_at,
            is_valid=session.is_valid
        )
    
    def get_session_by_id(self, session_id: str) -> Optional[DeviceSession]:
        return self.db.query(DeviceSession).filter(
            DeviceSession.session_id == session_id
        ).first()
    
    def get_sessions_by_device(self, device_id: str, skip: int = 0, limit: int = 100) -> List[DeviceSession]:
        return self.db.query(DeviceSession).filter(
            DeviceSession.device_id == device_id
        ).offset(skip).limit(limit).all()
    
    def get_all_sessions(self, skip: int = 0, limit: int = 100) -> List[DeviceSession]:
        return self.db.query(DeviceSession).offset(skip).limit(limit).all()
    
    def get_active_sessions(self, skip: int = 0, limit: int = 100) -> List[DeviceSession]:
        return self.db.query(DeviceSession).filter(
            and_(
                DeviceSession.is_valid == True,
                DeviceSession.is_active == True,
                DeviceSession.expires_at > datetime.utcnow()
            )
        ).offset(skip).limit(limit).all()
    
    def update_session(self, session_id: str, update_data: DeviceSessionUpdate) -> Optional[DeviceSession]:
        session = self.get_session_by_id(session_id)
        if not session:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(session, field, value)
        
        session.last_activity = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def validate_session(self, session_id: str, session_token: str = None) -> SessionValidateResponse:
        session = self.get_session_by_id(session_id)
        if not session:
            return SessionValidateResponse(
                session_id=session_id,
                is_valid=False,
                is_active=False,
                is_expired=True,
                is_compromised=False,
                requires_reauth=True,
                expires_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                message="Session not found"
            )
        
        # Check various validation conditions
        if session.is_expired():
            session.is_valid = False
            session.is_active = False
            self.db.commit()
            
            return SessionValidateResponse(
                session_id=session.session_id,
                is_valid=False,
                is_active=session.is_active,
                is_expired=True,
                is_compromised=session.is_compromised,
                requires_reauth=True,
                expires_at=session.expires_at,
                last_activity=session.last_activity,
                message="Session has expired"
            )
        
        if session.is_compromised:
            return SessionValidateResponse(
                session_id=session.session_id,
                is_valid=False,
                is_active=False,
                is_expired=False,
                is_compromised=True,
                requires_reauth=True,
                expires_at=session.expires_at,
                last_activity=session.last_activity,
                message="Session is compromised"
            )
        
        if not session.is_valid or not session.is_active:
            return SessionValidateResponse(
                session_id=session.session_id,
                is_valid=session.is_valid,
                is_active=session.is_active,
                is_expired=session.is_expired(),
                is_compromised=session.is_compromised,
                requires_reauth=session.requires_reauth,
                expires_at=session.expires_at,
                last_activity=session.last_activity,
                message="Session is invalid or inactive"
            )
        
        # Update last activity
        session.update_activity()
        self.db.commit()
        
        return SessionValidateResponse(
            session_id=session.session_id,
            is_valid=True,
            is_active=True,
            is_expired=False,
            is_compromised=False,
            requires_reauth=False,
            expires_at=session.expires_at,
            last_activity=session.last_activity,
            message="Session is valid"
        )
    
    def extend_session(self, extend_request: SessionExtendRequest) -> SessionExtendResponse:
        session = self.get_session_by_id(extend_request.session_id)
        if not session:
            raise ValueError("Session not found")
        
        if not session.is_valid_session():
            raise ValueError("Cannot extend invalid session")
        
        old_expires_at = session.expires_at
        session.extend_session(extend_request.extend_hours)
        
        self.db.commit()
        
        return SessionExtendResponse(
            session_id=session.session_id,
            old_expires_at=old_expires_at,
            new_expires_at=session.expires_at,
            extended_at=session.last_extended_at,
            message="Session extended successfully"
        )
    
    def revoke_session(self, revoke_request: SessionRevokeRequest) -> SessionRevokeResponse:
        session = self.get_session_by_id(revoke_request.session_id)
        if not session:
            raise ValueError("Session not found")
        
        session.revoke_session(revoke_request.reason)
        self.db.commit()
        
        return SessionRevokeResponse(
            session_id=session.session_id,
            revoked_at=session.revoked_at,
            reason=revoke_request.reason,
            message="Session revoked successfully"
        )
    
    def session_login(self, login_request: SessionLoginRequest) -> SessionLoginResponse:
        session = self.get_session_by_id(login_request.session_id)
        if not session:
            return SessionLoginResponse(
                session_id=login_request.session_id,
                login_successful=False,
                login_attempts_remaining=0,
                last_login_attempt=datetime.utcnow(),
                requires_reauth=True,
                message="Session not found"
            )
        
        if not session.can_login():
            return SessionLoginResponse(
                session_id=session.session_id,
                login_successful=False,
                login_attempts_remaining=0,
                last_login_attempt=session.last_login_attempt,
                requires_reauth=True,
                message="Account locked due to too many failed attempts"
            )
        
        # Simulate login validation (in real implementation, validate password/token)
        login_successful = True  # Simplified for demo
        
        if login_successful:
            session.successful_login()
            if login_request.ip_address:
                session.last_ip_address = login_request.ip_address
            
            self.db.commit()
            
            return SessionLoginResponse(
                session_id=session.session_id,
                login_successful=True,
                login_attempts_remaining=session.max_login_attempts - session.login_attempts,
                last_login_attempt=session.last_successful_login,
                requires_reauth=False,
                message="Login successful"
            )
        else:
            session.increment_login_attempt()
            self.db.commit()
            
            return SessionLoginResponse(
                session_id=session.session_id,
                login_successful=False,
                login_attempts_remaining=session.max_login_attempts - session.login_attempts,
                last_login_attempt=session.last_login_attempt,
                requires_reauth=session.requires_reauth,
                message="Invalid credentials"
            )
    
    def update_session_activity(self, activity_update: SessionActivityUpdate) -> bool:
        session = self.get_session_by_id(activity_update.session_id)
        if not session or not session.is_valid_session():
            return False
        
        session.update_activity(activity_update.ip_address)
        
        if activity_update.activity_type == "message_sent":
            session.increment_message_count()
        
        self.db.commit()
        return True
    
    def get_session_stats(self, session_id: str) -> SessionStats:
        session = self.get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Calculate uptime
        uptime_hours = 0.0
        if session.created_at:
            if session.revoked_at:
                uptime_hours = (session.revoked_at - session.created_at).total_seconds() / 3600
            else:
                uptime_hours = (datetime.utcnow() - session.created_at).total_seconds() / 3600
        
        # Calculate requests per hour
        requests_per_hour = 0.0
        if uptime_hours > 0:
            requests_per_hour = session.total_requests / uptime_hours
        
        # Determine status
        status = "active"
        if session.is_expired():
            status = "expired"
        elif session.revoked_at:
            status = "revoked"
        elif session.is_compromised:
            status = "compromised"
        
        return SessionStats(
            session_id=session.session_id,
            device_id=session.device_id,
            session_type=session.session_type,
            status=status,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_activity=session.last_activity,
            total_requests=session.total_requests,
            messages_sent_via_session=session.messages_sent_via_session,
            uptime_hours=uptime_hours,
            requests_per_hour=requests_per_hour
        )
    
    def get_device_session_stats(self, device_id: str) -> DeviceSessionStats:
        sessions = self.get_sessions_by_device(device_id)
        
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.is_valid_session()])
        expired_sessions = len([s for s in sessions if s.is_expired()])
        revoked_sessions = len([s for s in sessions if s.revoked_at])
        compromised_sessions = len([s for s in sessions if s.is_compromised])
        
        total_requests = sum(s.total_requests for s in sessions)
        total_messages_sent = sum(s.messages_sent_via_session for s in sessions)
        
        # Calculate average session duration
        durations = []
        for session in sessions:
            end_time = session.revoked_at or datetime.utcnow()
            duration = (end_time - session.created_at).total_seconds() / 3600
            durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        session_stats = []
        for session in sessions:
            stats = self.get_session_stats(session.session_id)
            session_stats.append(stats)
        
        return DeviceSessionStats(
            device_id=device_id,
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            expired_sessions=expired_sessions,
            revoked_sessions=revoked_sessions,
            compromised_sessions=compromised_sessions,
            total_requests=total_requests,
            total_messages_sent=total_messages_sent,
            average_session_duration=avg_duration,
            sessions=session_stats
        )
    
    def get_user_session_stats(self, user_id: str) -> UserSessionStats:
        # Get all devices for user
        devices = self.db.query(UnofficialLinkedDevice).filter(
            UnofficialLinkedDevice.user_id == user_id
        ).all()
        
        device_stats = []
        total_sessions = 0
        active_sessions = 0
        expired_sessions = 0
        revoked_sessions = 0
        compromised_sessions = 0
        total_requests = 0
        total_messages_sent = 0
        
        for device in devices:
            stats = self.get_device_session_stats(device.device_id)
            device_stats.append(stats)
            
            total_sessions += stats.total_sessions
            active_sessions += stats.active_sessions
            expired_sessions += stats.expired_sessions
            revoked_sessions += stats.revoked_sessions
            compromised_sessions += stats.compromised_sessions
            total_requests += stats.total_requests
            total_messages_sent += stats.total_messages_sent
        
        return UserSessionStats(
            user_id=user_id,
            total_devices=len(devices),
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            expired_sessions=expired_sessions,
            revoked_sessions=revoked_sessions,
            compromised_sessions=compromised_sessions,
            total_requests=total_requests,
            total_messages_sent=total_messages_sent,
            devices=device_stats
        )
    
    def bulk_session_operation(self, operation: BulkSessionOperation) -> dict:
        results = {"success": 0, "failed": 0, "details": []}
        
        for session_id in operation.session_ids:
            try:
                session = self.get_session_by_id(session_id)
                if not session:
                    results["failed"] += 1
                    results["details"].append(f"Session {session_id} not found")
                    continue
                
                if operation.operation == "revoke":
                    session.revoke_session(operation.parameters.get("reason") if operation.parameters else None)
                elif operation.operation == "extend":
                    hours = operation.parameters.get("hours", 24) if operation.parameters else 24
                    session.extend_session(hours)
                elif operation.operation == "deactivate":
                    session.is_active = False
                elif operation.operation == "reactivate":
                    if not session.is_expired() and not session.is_compromised:
                        session.is_active = True
                        session.is_valid = True
                
                self.db.commit()
                results["success"] += 1
                results["details"].append(f"Session {session_id} {operation.operation} successful")
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append(f"Session {session_id} failed: {str(e)}")
        
        return results
    
    def security_check(self, session_id: str) -> SessionSecurityCheck:
        session = self.get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        issues = []
        risk_level = "low"
        recommendations = []
        
        # Check for security issues
        if session.is_expired():
            issues.append("Session has expired")
            risk_level = "high"
        
        if session.is_compromised:
            issues.append("Session is compromised")
            risk_level = "critical"
        
        if session.login_attempts > 0:
            issues.append("Failed login attempts detected")
            risk_level = "medium"
        
        if session.total_requests > 10000:
            issues.append("High request volume detected")
            risk_level = "medium"
        
        if session.last_ip_address != session.ip_address and session.last_ip_address:
            issues.append("IP address changed during session")
            risk_level = "medium"
        
        # Generate recommendations
        if session.is_expired():
            recommendations.append("Create new session")
        
        if session.is_compromised:
            recommendations.append("Revoke all sessions for this device")
            recommendations.append("Change device credentials")
        
        if session.login_attempts > 0:
            recommendations.append("Monitor for suspicious activity")
        
        if risk_level in ["medium", "high", "critical"]:
            recommendations.append("Enable multi-factor authentication")
        
        return SessionSecurityCheck(
            session_id=session.session_id,
            security_issues=issues,
            risk_level=risk_level,
            recommendations=recommendations,
            last_check=datetime.utcnow()
        )
    
    def health_check(self, session_id: str) -> SessionHealthCheck:
        session = self.get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        issues = []
        health_score = 1.0
        
        # Calculate health score
        if session.is_expired():
            health_score -= 0.5
            issues.append("Session expired")
        
        if session.is_compromised:
            health_score -= 0.8
            issues.append("Session compromised")
        
        if not session.is_valid or not session.is_active:
            health_score -= 0.3
            issues.append("Session invalid or inactive")
        
        if session.login_attempts > 3:
            health_score -= 0.2
            issues.append("Multiple failed login attempts")
        
        # Check session age
        session_age_hours = (datetime.utcnow() - session.created_at).total_seconds() / 3600
        if session_age_hours > 48:  # Older than 2 days
            health_score -= 0.1
            issues.append("Session is older than 48 hours")
        
        health_score = max(0.0, health_score)
        
        # Generate recommendations
        recommendations = []
        if health_score < 0.5:
            recommendations.append("Consider revoking and creating new session")
        elif health_score < 0.8:
            recommendations.append("Monitor session activity closely")
        
        if session.is_expired():
            recommendations.append("Create new session")
        
        return SessionHealthCheck(
            session_id=session.session_id,
            is_healthy=health_score >= 0.7,
            health_score=health_score,
            issues=issues,
            recommendations=recommendations,
            last_check=datetime.utcnow()
        )
    
    def cleanup_sessions(self, cleanup_request: SessionCleanupRequest) -> SessionCleanupResponse:
        sessions_cleaned = 0
        sessions_affected = []
        
        if cleanup_request.cleanup_type == "expired":
            expired_sessions = self.db.query(DeviceSession).filter(
                and_(
                    DeviceSession.expires_at < datetime.utcnow(),
                    DeviceSession.is_valid == True
                )
            ).all()
            
            for session in expired_sessions:
                if not cleanup_request.dry_run:
                    session.is_valid = False
                    session.is_active = False
                sessions_cleaned += 1
                sessions_affected.append(session.session_id)
        
        elif cleanup_request.cleanup_type == "inactive":
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            inactive_sessions = self.db.query(DeviceSession).filter(
                and_(
                    DeviceSession.last_activity < cutoff_time,
                    DeviceSession.is_valid == True,
                    DeviceSession.is_active == True
                )
            ).all()
            
            for session in inactive_sessions:
                if not cleanup_request.dry_run:
                    session.is_active = False
                sessions_cleaned += 1
                sessions_affected.append(session.session_id)
        
        elif cleanup_request.cleanup_type == "compromised":
            compromised_sessions = self.db.query(DeviceSession).filter(
                DeviceSession.is_compromised == True
            ).all()
            
            for session in compromised_sessions:
                if not cleanup_request.dry_run:
                    session.is_valid = False
                    session.is_active = False
                sessions_cleaned += 1
                sessions_affected.append(session.session_id)
        
        if not cleanup_request.dry_run:
            self.db.commit()
        
        return SessionCleanupResponse(
            cleanup_type=cleanup_request.cleanup_type,
            sessions_cleaned=sessions_cleaned,
            sessions_affected=sessions_affected,
            cleanup_time=datetime.utcnow(),
            dry_run=cleanup_request.dry_run,
            message=f"{'Dry run completed' if cleanup_request.dry_run else 'Cleanup completed'} for {sessions_cleaned} sessions"
        )
