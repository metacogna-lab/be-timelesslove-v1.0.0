-- Migration: Analytics Events and Metrics Tables
-- Purpose: Create tables for storing analytics events and metrics
-- Note: This file is for documentation. Apply changes via Supabase dashboard or migration tools.

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id UUID UNIQUE NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  family_unit_id UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
  session_id UUID,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object')
);

-- Create analytics_metrics table
CREATE TABLE IF NOT EXISTS analytics_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  metric_name VARCHAR(100) NOT NULL,
  metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('count', 'gauge', 'histogram', 'timer')),
  value NUMERIC NOT NULL,
  labels JSONB DEFAULT '{}'::jsonb,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT valid_labels CHECK (jsonb_typeof(labels) = 'object'),
  CONSTRAINT positive_value CHECK (value >= 0)
);

-- Create indexes for analytics_events
CREATE INDEX idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_family_unit_id ON analytics_events(family_unit_id);
CREATE INDEX idx_analytics_events_session_id ON analytics_events(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_analytics_events_metadata ON analytics_events USING GIN(metadata);

-- Create composite index for common queries
CREATE INDEX idx_analytics_events_type_timestamp ON analytics_events(event_type, timestamp DESC);

-- Create indexes for analytics_metrics
CREATE INDEX idx_analytics_metrics_metric_name ON analytics_metrics(metric_name);
CREATE INDEX idx_analytics_metrics_timestamp ON analytics_metrics(timestamp);
CREATE INDEX idx_analytics_metrics_metric_type ON analytics_metrics(metric_type);
CREATE INDEX idx_analytics_metrics_labels ON analytics_metrics USING GIN(labels);

-- Create composite index for common queries
CREATE INDEX idx_analytics_metrics_name_timestamp ON analytics_metrics(metric_name, timestamp DESC);

-- Enable Row Level Security
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_metrics ENABLE ROW LEVEL SECURITY;

-- RLS Policies for analytics_events
-- Users can view events for their family
CREATE POLICY "Users can view events for their family"
  ON analytics_events FOR SELECT
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
  );

-- Service role can insert events (for backend logging)
CREATE POLICY "Service can insert events"
  ON analytics_events FOR INSERT
  WITH CHECK (true);  -- Service role bypasses RLS

-- RLS Policies for analytics_metrics
-- Users can view metrics for their family
CREATE POLICY "Users can view metrics for their family"
  ON analytics_metrics FOR SELECT
  USING (
    labels->>'family_unit_id' IN (
      SELECT family_unit_id::text 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
    OR labels->>'family_unit_id' IS NULL  -- Global metrics
  );

-- Service role can insert metrics (for backend logging)
CREATE POLICY "Service can insert metrics"
  ON analytics_metrics FOR INSERT
  WITH CHECK (true);  -- Service role bypasses RLS

