-- Migration: Memory and Media Tables
-- Purpose: Create tables for memories and associated media files
-- Note: This file is for documentation. Apply changes via Supabase dashboard or migration tools.

-- Create memory status enum
CREATE TYPE memory_status AS ENUM (
  'draft',
  'published',
  'archived'
);

-- Create processing status enum
CREATE TYPE processing_status AS ENUM (
  'pending',
  'processing',
  'completed',
  'failed'
);

-- Create memories table
CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  family_unit_id UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
  title VARCHAR(255),
  description TEXT,
  memory_date DATE,
  location VARCHAR(255),
  tags TEXT[] DEFAULT '{}',
  status memory_status DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  modified_by UUID REFERENCES auth.users(id)
);

-- Create memory_media table
CREATE TABLE IF NOT EXISTS memory_media (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  storage_path TEXT NOT NULL,
  storage_bucket VARCHAR(100) DEFAULT 'memories',
  file_name VARCHAR(255) NOT NULL,
  mime_type VARCHAR(100) NOT NULL,
  file_size BIGINT NOT NULL,
  width INTEGER,
  height INTEGER,
  duration INTEGER,
  thumbnail_path TEXT,
  processing_status processing_status DEFAULT 'pending',
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT valid_file_size CHECK (file_size > 0),
  CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object')
);

-- Create indexes
CREATE INDEX idx_memories_family_unit_id ON memories(family_unit_id);
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_status ON memories(status);
CREATE INDEX idx_memory_media_memory_id ON memory_media(memory_id);
CREATE INDEX idx_memory_media_processing_status ON memory_media(processing_status);

-- Create GIN index on tags for efficient array queries
CREATE INDEX idx_memories_tags ON memories USING GIN(tags);

-- Create GIN index on metadata for efficient JSONB queries
CREATE INDEX idx_memory_media_metadata ON memory_media USING GIN(metadata);

-- Apply updated_at triggers
CREATE TRIGGER update_memories_updated_at
  BEFORE UPDATE ON memories
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_media_updated_at
  BEFORE UPDATE ON memory_media
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_media ENABLE ROW LEVEL SECURITY;

-- RLS Policies for memories
CREATE POLICY "Users can view memories in their family"
  ON memories FOR SELECT
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
  );

CREATE POLICY "Users can create memories in their family"
  ON memories FOR INSERT
  WITH CHECK (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
    AND user_id = auth.uid()
  );

CREATE POLICY "Users can update their own memories or adults can update any in family"
  ON memories FOR UPDATE
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
    AND (
      user_id = auth.uid()
      OR EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid()
        AND role = 'adult'
        AND family_unit_id = memories.family_unit_id
      )
    )
  );

CREATE POLICY "Users can delete their own memories or adults can delete any in family"
  ON memories FOR DELETE
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
    AND (
      user_id = auth.uid()
      OR EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid()
        AND role = 'adult'
        AND family_unit_id = memories.family_unit_id
      )
    )
  );

-- RLS Policies for memory_media
CREATE POLICY "Users can view media for memories in their family"
  ON memory_media FOR SELECT
  USING (
    memory_id IN (
      SELECT id FROM memories
      WHERE family_unit_id IN (
        SELECT family_unit_id 
        FROM user_profiles 
        WHERE id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can create media for memories they can modify"
  ON memory_media FOR INSERT
  WITH CHECK (
    memory_id IN (
      SELECT id FROM memories
      WHERE family_unit_id IN (
        SELECT family_unit_id 
        FROM user_profiles 
        WHERE id = auth.uid()
      )
      AND (
        user_id = auth.uid()
        OR EXISTS (
          SELECT 1 FROM user_profiles
          WHERE id = auth.uid()
          AND role = 'adult'
          AND family_unit_id = memories.family_unit_id
        )
      )
    )
  );

CREATE POLICY "Users can update media for memories they can modify"
  ON memory_media FOR UPDATE
  USING (
    memory_id IN (
      SELECT id FROM memories
      WHERE family_unit_id IN (
        SELECT family_unit_id 
        FROM user_profiles 
        WHERE id = auth.uid()
      )
      AND (
        user_id = auth.uid()
        OR EXISTS (
          SELECT 1 FROM user_profiles
          WHERE id = auth.uid()
          AND role = 'adult'
          AND family_unit_id = memories.family_unit_id
        )
      )
    )
  );

CREATE POLICY "Users can delete media for memories they can modify"
  ON memory_media FOR DELETE
  USING (
    memory_id IN (
      SELECT id FROM memories
      WHERE family_unit_id IN (
        SELECT family_unit_id 
        FROM user_profiles 
        WHERE id = auth.uid()
      )
      AND (
        user_id = auth.uid()
        OR EXISTS (
          SELECT 1 FROM user_profiles
          WHERE id = auth.uid()
          AND role = 'adult'
          AND family_unit_id = memories.family_unit_id
        )
      )
    )
  );

