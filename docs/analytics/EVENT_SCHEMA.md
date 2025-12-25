# Analytics Event Schema Documentation

## Overview

Timeless Love emits structured events for all major domain actions to support analytics, monitoring, and future intelligence systems. All events follow a consistent schema with stable field names, timestamps, and correlated IDs.

## Event Schema Structure

All events share a common base structure:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "memory_posted",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "family_unit_id": "550e8400-e29b-41d4-a716-446655440002",
  "session_id": "550e8400-e29b-41d4-a716-446655440003",
  "metadata": {
    // Event-specific metadata
  }
}
```

### Base Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID | Yes | Unique identifier for the event |
| `event_type` | string | Yes | Type of event (see Event Types below) |
| `timestamp` | ISO 8601 | Yes | Event timestamp (UTC) |
| `user_id` | UUID | Yes | User who triggered the event |
| `family_unit_id` | UUID | Yes | Family unit context |
| `session_id` | UUID | No | Session identifier for request correlation |
| `metadata` | object | Yes | Event-specific data (can be empty) |

## Event Types

### Authentication Events

#### `user_registered`

Emitted when a new user registers.

```json
{
  "event_id": "...",
  "event_type": "user_registered",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "role": "adult",
    "is_family_creator": true,
    "registration_method": "self_signup"
  }
}
```

#### `user_logged_in`

Emitted when a user successfully logs in.

```json
{
  "event_id": "...",
  "event_type": "user_logged_in",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "login_method": "email_password",
    "device_type": "web"
  }
}
```

#### `user_logged_out`

Emitted when a user logs out.

```json
{
  "event_id": "...",
  "event_type": "user_logged_out",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {}
}
```

### Memory Events

#### `memory_posted`

Emitted when a memory is created and published.

```json
{
  "event_id": "...",
  "event_type": "memory_posted",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "title": "Family Vacation 2024",
    "media_count": 3,
    "has_location": true,
    "tag_count": 2
  }
}
```

#### `memory_updated`

Emitted when a memory is updated.

```json
{
  "event_id": "...",
  "event_type": "memory_updated",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "updated_fields": ["title", "description"]
  }
}
```

#### `memory_deleted`

Emitted when a memory is deleted.

```json
{
  "event_id": "...",
  "event_type": "memory_deleted",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "deleted_by_owner": true
  }
}
```

#### `memory_viewed`

Emitted when a user views a memory detail page.

```json
{
  "event_id": "...",
  "event_type": "memory_viewed",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "view_duration_ms": 5000
  }
}
```

### Interaction Events

#### `reaction_created`

Emitted when a user creates a reaction.

```json
{
  "event_id": "...",
  "event_type": "reaction_created",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "reaction_id": "550e8400-e29b-41d4-a716-446655440005",
    "emoji": "👍"
  }
}
```

#### `reaction_deleted`

Emitted when a user deletes a reaction.

```json
{
  "event_id": "...",
  "event_type": "reaction_deleted",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "reaction_id": "550e8400-e29b-41d4-a716-446655440005",
    "emoji": "👍"
  }
}
```

#### `comment_created`

Emitted when a user creates a comment.

```json
{
  "event_id": "...",
  "event_type": "comment_created",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "comment_id": "550e8400-e29b-41d4-a716-446655440006",
    "parent_comment_id": null,
    "is_reply": false,
    "content_length": 50
  }
}
```

#### `comment_updated`

Emitted when a user updates a comment.

```json
{
  "event_id": "...",
  "event_type": "comment_updated",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "comment_id": "550e8400-e29b-41d4-a716-446655440006"
  }
}
```

#### `comment_deleted`

Emitted when a user deletes a comment.

```json
{
  "event_id": "...",
  "event_type": "comment_deleted",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "memory_id": "550e8400-e29b-41d4-a716-446655440004",
    "comment_id": "550e8400-e29b-41d4-a716-446655440006",
    "deleted_by_owner": true
  }
}
```

### Feed Events

#### `feed_viewed`

Emitted when a user views the feed.

```json
{
  "event_id": "...",
  "event_type": "feed_viewed",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "page": 1,
    "page_size": 20,
    "filters": {
      "status": "published",
      "tags": ["vacation"]
    },
    "items_returned": 15
  }
}
```

### Family Management Events

#### `invite_created`

Emitted when an adult creates an invitation.

```json
{
  "event_id": "...",
  "event_type": "invite_created",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "invite_id": "550e8400-e29b-41d4-a716-446655440007",
    "invited_email": "user@example.com",
    "invited_role": "teen"
  }
}
```

#### `invite_accepted`

Emitted when an invitation is accepted.

```json
{
  "event_id": "...",
  "event_type": "invite_accepted",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "invite_id": "550e8400-e29b-41d4-a716-446655440007",
    "accepted_role": "teen"
  }
}
```

#### `child_provisioned`

Emitted when an adult provisions a child account.

```json
{
  "event_id": "...",
  "event_type": "child_provisioned",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "provisioned_user_id": "550e8400-e29b-41d4-a716-446655440008",
    "display_name": "Child Name"
  }
}
```

#### `pet_created`

Emitted when a pet profile is created.

```json
{
  "event_id": "...",
  "event_type": "pet_created",
  "timestamp": "2024-07-15T10:00:00Z",
  "user_id": "...",
  "family_unit_id": "...",
  "metadata": {
    "pet_user_id": "550e8400-e29b-41d4-a716-446655440009",
    "display_name": "Fluffy"
  }
}
```

## Event Storage

Events are stored in the `analytics_events` table in Supabase with the following schema:

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

CREATE INDEX idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_family_unit_id ON analytics_events(family_unit_id);
CREATE INDEX idx_analytics_events_metadata ON analytics_events USING GIN(metadata);
```

## Metrics Schema

Metrics are stored in the `analytics_metrics` table:

```sql
CREATE TABLE analytics_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  metric_name VARCHAR(100) NOT NULL,
  metric_type VARCHAR(50) NOT NULL, -- 'count', 'gauge', 'histogram', 'timer'
  value NUMERIC NOT NULL,
  labels JSONB DEFAULT '{}'::jsonb,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analytics_metrics_metric_name ON analytics_metrics(metric_name);
CREATE INDEX idx_analytics_metrics_timestamp ON analytics_metrics(timestamp);
CREATE INDEX idx_analytics_metrics_labels ON analytics_metrics USING GIN(labels);
```

## Usage Guidelines

1. **Always include required fields**: event_id, event_type, timestamp, user_id, family_unit_id
2. **Use consistent event types**: Follow the naming convention (snake_case)
3. **Include relevant metadata**: Add context-specific data in metadata field
4. **Don't log sensitive data**: Never include passwords, tokens, or PII in events
5. **Use UTC timestamps**: All timestamps must be in UTC
6. **Correlate with session_id**: Include session_id for request tracing

## Future Intelligence Integration

Events are designed to support future AI/ML features:
- User behavior analysis
- Content recommendation
- Engagement prediction
- Anomaly detection
- Personalization

All events include stable field names and structured metadata to enable machine learning consumption.

