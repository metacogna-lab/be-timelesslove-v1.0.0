---
title: Analytics
description: Event logging and metrics collection system
sidebar:
  order: 8
---

# Analytics

The analytics system provides structured event logging and metrics collection for monitoring, analysis, and future intelligence features.

## Overview

The analytics system consists of two main components:

1. **Events**: Structured event logging for user actions and system events
2. **Metrics**: Performance and usage metrics (counters, gauges, timers)

## Concepts

### Events

Events represent discrete actions that occur in the system:

- **Event Type**: Categorizes the event (e.g., `memory_posted`, `reaction_created`)
- **Metadata**: Flexible JSONB field for event-specific data
- **Context**: User ID, family unit ID, session ID
- **Timestamp**: When the event occurred

### Metrics

Metrics represent measurements over time:

- **Counters**: Cumulative values that only increase
- **Gauges**: Current values that can increase or decrease
- **Timers**: Duration measurements
- **Histograms**: Distribution of values

## Event System

### Standard Events

The system automatically emits events for:

**Authentication:**
- `user_registered`
- `user_logged_in`
- `user_logged_out`

**Memories:**
- `memory_posted`
- `memory_updated`
- `memory_deleted`
- `memory_viewed`

**Interactions:**
- `reaction_created`
- `reaction_deleted`
- `comment_created`
- `comment_updated`
- `comment_deleted`

**Feed:**
- `feed_viewed`

**Family Management:**
- `invite_created`
- `invite_accepted`
- `child_provisioned`
- `pet_created`

### Emitting Events

```python
from app.services.analytics_service import get_analytics_service

analytics = get_analytics_service()

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

### Event Structure

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "event_type": "memory_posted",
  "timestamp": "2024-01-20T12:00:00Z",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "family_unit_id": "660e8400-e29b-41d4-a716-446655440003",
  "session_id": "770e8400-e29b-41d4-a716-446655440004",
  "metadata": {
    "memory_id": "880e8400-e29b-41d4-a716-446655440005",
    "title": "Family Vacation",
    "media_count": 3
  },
  "created_at": "2024-01-20T12:00:00Z"
}
```

## Metrics System

### Counter Metrics

Counters track cumulative values:

```python
await analytics.increment_counter(
    metric_name="api_request_count",
    labels={"endpoint": "/api/v1/memories", "method": "POST"}
)
```

### Gauge Metrics

Gauges track current values:

```python
await analytics.record_gauge(
    metric_name="active_users",
    value=150,
    labels={"family_unit_id": str(family_unit_id)}
)
```

### Timer Metrics

Timers track duration:

```python
start_time = time.time()
# ... perform operation ...
duration_ms = (time.time() - start_time) * 1000

await analytics.record_timer(
    metric_name="api_request_duration_ms",
    duration_ms=duration_ms,
    labels={"endpoint": "/api/v1/feed"}
)
```

### Histogram Metrics

Histograms track distribution:

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

- **API Request Metrics**: Count, duration, error rates for all endpoints
- **Request Correlation**: Request IDs for tracing requests
- **User Context**: User ID, family unit ID, role for all events

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
  labels->>'endpoint' as endpoint,
  SUM(value) as total_requests
FROM analytics_metrics
WHERE metric_name = 'api_request_count'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY labels->>'endpoint'
ORDER BY total_requests DESC;

-- Get average response times
SELECT 
  labels->>'endpoint' as endpoint,
  AVG(value) as avg_duration_ms
FROM analytics_metrics
WHERE metric_name = 'api_request_duration_ms'
  AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY labels->>'endpoint'
ORDER BY avg_duration_ms DESC;
```

## Integration Patterns

### Background Task Logging

Events are logged asynchronously to avoid blocking requests:

```python
from fastapi import BackgroundTasks

@router.post("/memories")
async def create_memory(
    request: CreateMemoryRequest,
    current_user: CurrentUser = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    memory = await memory_service.create_memory(...)
    
    # Log event in background
    background_tasks.add_task(
        log_memory_posted,
        user_id=current_user.user_id,
        family_unit_id=current_user.family_unit_id,
        memory_id=memory.id
    )
    
    return memory
```

### Service-Level Logging

```python
from app.services.metrics import log_feed_interaction

# Log feed interaction
await log_feed_interaction(
    user_id=user_id,
    family_unit_id=family_unit_id,
    interaction_type="reaction_created",
    metadata={"memory_id": str(memory_id), "emoji": "👍"}
)
```

## Best Practices

### Event Emission

1. **Use Background Tasks**: Always emit events in background tasks
2. **Include Relevant Metadata**: Add context-specific data in metadata
3. **Don't Log Sensitive Data**: Never include passwords, tokens, or PII
4. **Use Consistent Naming**: Follow snake_case for event types
5. **Handle Errors Gracefully**: Analytics failures should not break the application

### Metrics Collection

1. **Use Labels for Filtering**: Add labels to metrics for easy filtering
2. **Choose Appropriate Types**: Use counters for counts, gauges for current values
3. **Normalize Values**: Use consistent units (milliseconds, bytes, etc.)
4. **Batch When Possible**: Batch metric writes for performance

### Querying

1. **Use Indexes**: Leverage database indexes on event_type, timestamp, user_id
2. **Filter by Time Range**: Always filter by timestamp for performance
3. **Use JSONB Queries**: Query metadata fields efficiently
4. **Aggregate When Possible**: Use GROUP BY for summaries

## Future Intelligence Integration

Events are designed to support future AI/ML features:

- **User Behavior Analysis**: Track user patterns and preferences
- **Content Recommendation**: Analyze engagement to suggest relevant content
- **Anomaly Detection**: Identify unusual patterns or security issues
- **Personalization**: Customize experiences based on user history

All events include:
- Stable field names
- Structured metadata
- Timestamps
- User and family context

## Database Schema

### Events Table

```sql
CREATE TABLE analytics_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id UUID UNIQUE NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  family_unit_id UUID NOT NULL REFERENCES family_units(id),
  session_id UUID,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Metrics Table

```sql
CREATE TABLE analytics_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  metric_name VARCHAR(100) NOT NULL,
  metric_type VARCHAR(50) NOT NULL,
  value NUMERIC NOT NULL,
  labels JSONB DEFAULT '{}'::jsonb,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Related Documentation

- [Analytics Usage Guide](../analytics/USAGE.md)
- [Event Schema](../analytics/EVENT_SCHEMA.md)
- [Database Schema](../database/)

