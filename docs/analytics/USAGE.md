# Analytics Usage Guide

## Overview

The Timeless Love analytics system provides structured event logging and metrics collection for monitoring, analysis, and future intelligence features.

## Quick Start

### Emitting Events

```python
from app.services.analytics_service import get_analytics_service

analytics = get_analytics_service()

# Emit a custom event
await analytics.emit_event(
    event_type="memory_posted",
    user_id=user_id,
    family_unit_id=family_unit_id,
    metadata={
        "memory_id": str(memory_id),
        "title": "Family Vacation",
        "media_count": 3
    }
)
```

### Recording Metrics

```python
# Increment a counter
await analytics.increment_counter(
    metric_name="api_request_count",
    labels={"endpoint": "/api/v1/memories", "method": "POST"}
)

# Record a gauge (current value)
await analytics.record_gauge(
    metric_name="active_users",
    value=150,
    labels={"family_unit_id": str(family_unit_id)}
)

# Record a timer (duration in milliseconds)
await analytics.record_timer(
    metric_name="api_request_duration_ms",
    duration_ms=125.5,
    labels={"endpoint": "/api/v1/feed"}
)
```

## Event Types

### Standard Events

The system automatically emits events for:

- **Authentication**: `user_registered`, `user_logged_in`, `user_logged_out`
- **Memories**: `memory_posted`, `memory_updated`, `memory_deleted`, `memory_viewed`
- **Interactions**: `reaction_created`, `reaction_deleted`, `comment_created`, `comment_updated`, `comment_deleted`
- **Feed**: `feed_viewed`
- **Family Management**: `invite_created`, `invite_accepted`, `child_provisioned`, `pet_created`

### Custom Events

You can emit custom events for domain-specific actions:

```python
await analytics.emit_event(
    event_type="custom_action",
    user_id=user_id,
    family_unit_id=family_unit_id,
    metadata={
        "custom_field": "value",
        "another_field": 123
    }
)
```

## Metrics Types

### Counters

Counters track cumulative values that only increase:

```python
await analytics.increment_counter(
    metric_name="memory_uploads",
    value=1.0,
    labels={"family_unit_id": str(family_unit_id)}
)
```

### Gauges

Gauges track current values that can increase or decrease:

```python
await analytics.record_gauge(
    metric_name="active_sessions",
    value=current_session_count,
    labels={"family_unit_id": str(family_unit_id)}
)
```

### Timers

Timers track duration measurements:

```python
start_time = time.time()
# ... perform operation ...
duration_ms = (time.time() - start_time) * 1000

await analytics.record_timer(
    metric_name="operation_duration_ms",
    duration_ms=duration_ms,
    labels={"operation": "memory_processing"}
)
```

### Histograms

Histograms track distribution of values:

```python
await analytics.record_metric(
    metric_name="memory_size_bytes",
    metric_type="histogram",
    value=file_size,
    labels={"mime_type": "image/jpeg"}
)
```

## Automatic Metrics

The system automatically collects:

- **API Request Metrics**: Count, duration, and error rates for all endpoints
- **Request Correlation**: Request IDs for tracing requests across services
- **User Context**: User ID, family unit ID, and role for all events

## Querying Analytics

### Query Events

```sql
-- Get all memory posts in the last 24 hours
SELECT * FROM analytics_events
WHERE event_type = 'memory_posted'
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Get events for a specific user
SELECT * FROM analytics_events
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY timestamp DESC;

-- Get events for a family unit
SELECT * FROM analytics_events
WHERE family_unit_id = '660e8400-e29b-41d4-a716-446655440001'
ORDER BY timestamp DESC;
```

### Query Metrics

```sql
-- Get API request counts by endpoint
SELECT 
  labels->>'path' as endpoint,
  SUM(value) as total_requests
FROM analytics_metrics
WHERE metric_name = 'api_request_count'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY labels->>'path'
ORDER BY total_requests DESC;

-- Get average response times
SELECT 
  labels->>'path' as endpoint,
  AVG(value) as avg_duration_ms
FROM analytics_metrics
WHERE metric_name = 'api_request_duration_ms'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY labels->>'path'
ORDER BY avg_duration_ms DESC;
```

## Best Practices

1. **Use Background Tasks**: Always emit events/metrics in background tasks to avoid blocking requests
2. **Include Relevant Metadata**: Add context-specific data in metadata fields
3. **Use Labels for Filtering**: Add labels to metrics for easy filtering and grouping
4. **Don't Log Sensitive Data**: Never include passwords, tokens, or PII in events
5. **Use Consistent Naming**: Follow snake_case for event types and metric names
6. **Handle Errors Gracefully**: Analytics failures should not break the application

## Integration with Intelligence Systems

Events are designed to support future AI/ML features:

- **User Behavior Analysis**: Track user patterns and preferences
- **Content Recommendation**: Analyze engagement to suggest relevant content
- **Anomaly Detection**: Identify unusual patterns or security issues
- **Personalization**: Customize experiences based on user history

All events include stable field names and structured metadata for machine learning consumption.

## Dashboard Integration

Analytics data can be visualized in dashboards:

1. **Event Streams**: Real-time event monitoring
2. **Metrics Dashboards**: Performance and usage metrics
3. **User Analytics**: User behavior and engagement
4. **Family Analytics**: Family-level insights

## Performance Considerations

- Events are stored asynchronously to avoid blocking requests
- Metrics are batched when possible
- Indexes are optimized for common query patterns
- Old data can be archived or deleted based on retention policies

