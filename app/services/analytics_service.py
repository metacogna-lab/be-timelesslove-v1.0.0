"""
Service for analytics event and metric collection.
"""

from uuid import UUID, uuid4
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from app.db.supabase import get_supabase_service_client
from app.models.analytics import AnalyticsEvent, AnalyticsMetric


logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
    
    async def emit_event(
        self,
        event_type: str,
        user_id: UUID,
        family_unit_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[UUID] = None
    ) -> UUID:
        """
        Emit an analytics event.
        
        Args:
            event_type: Type of event (e.g., "memory_posted", "reaction_created")
            user_id: User ID who triggered the event
            family_unit_id: Family unit context
            metadata: Event-specific metadata
            session_id: Optional session identifier
            
        Returns:
            Event ID (UUID)
        """
        event_id = uuid4()
        timestamp = datetime.utcnow()
        
        try:
            event_data = {
                "event_id": str(event_id),
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
                "user_id": str(user_id),
                "family_unit_id": str(family_unit_id),
                "metadata": metadata or {}
            }
            
            if session_id:
                event_data["session_id"] = str(session_id)
            
            # Insert into database
            result = self.supabase.table("analytics_events").insert(event_data).execute()
            
            if not result.data:
                logger.error(f"Failed to insert analytics event: {event_type}")
                return event_id
            
            # Also log to structured logging
            logger.info(
                "Analytics event emitted",
                extra={
                    "event_id": str(event_id),
                    "event_type": event_type,
                    "user_id": str(user_id),
                    "family_unit_id": str(family_unit_id),
                    "metadata": metadata or {}
                }
            )
            
            return event_id
            
        except Exception as e:
            # Don't fail the request if event logging fails
            logger.error(f"Failed to emit analytics event: {e}", exc_info=True)
            return event_id
    
    async def record_metric(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> UUID:
        """
        Record an analytics metric.
        
        Args:
            metric_name: Name of the metric (e.g., "api_request_count", "response_time_ms")
            metric_type: Type of metric ('count', 'gauge', 'histogram', 'timer')
            value: Metric value
            labels: Optional labels for filtering/grouping
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Metric record ID (UUID)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            metric_data = {
                "metric_name": metric_name,
                "metric_type": metric_type,
                "value": float(value),
                "labels": labels or {},
                "timestamp": timestamp.isoformat()
            }
            
            # Insert into database
            result = self.supabase.table("analytics_metrics").insert(metric_data).execute()

            if not result.data or len(result.data) == 0:
                logger.error(f"Failed to insert analytics metric: {metric_name}")
                return uuid4()

            # Also log to structured logging
            logger.info(
                "Analytics metric recorded",
                extra={
                    "metric_name": metric_name,
                    "metric_type": metric_type,
                    "value": value,
                    "labels": labels or {}
                }
            )

            # Extract ID from response - handle different response formats
            inserted_row = result.data[0]
            if isinstance(inserted_row, dict) and "id" in inserted_row:
                id_value = inserted_row["id"]
                if isinstance(id_value, str):
                    return UUID(id_value)
                else:
                    # Convert to string if needed
                    return UUID(str(id_value))
            else:
                # Fallback if response format is unexpected
                logger.warning(f"Unexpected response format for analytics metric: {inserted_row}")
                return uuid4()
            
        except Exception as e:
            # Don't fail the request if metric logging fails
            logger.error(f"Failed to record analytics metric: {e}", exc_info=True)
            return uuid4()
    
    async def increment_counter(
        self,
        metric_name: str,
        labels: Optional[Dict[str, Any]] = None,
        value: float = 1.0
    ) -> UUID:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the counter
            labels: Optional labels
            value: Increment value (default 1.0)
            
        Returns:
            Metric record ID
        """
        return await self.record_metric(
            metric_name=metric_name,
            metric_type="count",
            value=value,
            labels=labels
        )
    
    async def record_gauge(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Record a gauge metric (current value).
        
        Args:
            metric_name: Name of the gauge
            value: Current value
            labels: Optional labels
            
        Returns:
            Metric record ID
        """
        return await self.record_metric(
            metric_name=metric_name,
            metric_type="gauge",
            value=value,
            labels=labels
        )
    
    async def record_timer(
        self,
        metric_name: str,
        duration_ms: float,
        labels: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Record a timer metric (duration in milliseconds).
        
        Args:
            metric_name: Name of the timer
            duration_ms: Duration in milliseconds
            labels: Optional labels
            
        Returns:
            Metric record ID
        """
        return await self.record_metric(
            metric_name=metric_name,
            metric_type="timer",
            value=duration_ms,
            labels=labels
        )


# Global analytics service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service

