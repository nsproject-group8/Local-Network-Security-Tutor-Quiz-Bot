from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path
from loguru import logger
from config import settings

class AuditLogger:
    """
    Audit logging for security and privacy compliance.
    Tracks all data access and modifications.
    """
    
    def __init__(self):
        self.enabled = settings.ENABLE_AUDIT_LOGGING
        self.audit_file = Path(settings.LOGS_PATH) / "audit.log"
        
        # Ensure logs directory exists
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.enabled:
            logger.info(f"Audit logging enabled: {self.audit_file}")
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        action: str = "",
        resource: str = "",
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'data_access', 'data_modification')
            user_id: Identifier for the user
            action: Action performed (e.g., 'query', 'upload', 'delete')
            resource: Resource accessed (e.g., 'documents', 'quiz')
            details: Additional event details
            status: Event status (success/failure)
        """
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id or 'anonymous',
            'action': action,
            'resource': resource,
            'status': status,
            'details': details or {}
        }
        
        try:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")
    
    def log_data_access(
        self,
        resource: str,
        action: str,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        results_count: int = 0
    ):
        """Log data access events."""
        self.log_event(
            event_type='data_access',
            user_id=user_id,
            action=action,
            resource=resource,
            details={
                'query': query,
                'results_count': results_count
            }
        )
    
    def log_data_modification(
        self,
        resource: str,
        action: str,
        user_id: Optional[str] = None,
        items_affected: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log data modification events."""
        self.log_event(
            event_type='data_modification',
            user_id=user_id,
            action=action,
            resource=resource,
            details={
                'items_affected': items_affected,
                **(details or {})
            }
        )
    
    def log_security_event(
        self,
        action: str,
        user_id: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security-related events."""
        self.log_event(
            event_type='security',
            user_id=user_id,
            action=action,
            resource='system',
            status=status,
            details=details
        )
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        status_code: int = 200,
        response_time_ms: Optional[float] = None
    ):
        """Log API requests for monitoring."""
        self.log_event(
            event_type='api_request',
            user_id=user_id,
            action=method,
            resource=endpoint,
            status='success' if status_code < 400 else 'failure',
            details={
                'status_code': status_code,
                'response_time_ms': response_time_ms
            }
        )
    
    def get_recent_events(self, n: int = 100) -> list:
        """
        Retrieve recent audit events.
        
        Args:
            n: Number of recent events to retrieve
            
        Returns:
            List of audit events
        """
        if not self.audit_file.exists():
            return []
        
        try:
            events = []
            with open(self.audit_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-n:]:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return events
        except Exception as e:
            logger.error(f"Error reading audit log: {e}")
            return []

# Singleton instance
audit_logger = AuditLogger()
