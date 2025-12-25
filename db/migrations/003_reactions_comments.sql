-- Migration: Reactions and Comments Tables
-- Purpose: Create tables for memory reactions and threaded comments
-- Note: This file is for documentation. Apply changes via Supabase dashboard or migration tools.

-- Create reaction_emoji enum (common emoji types)
-- Note: We'll store emoji as VARCHAR to allow flexibility, but validate against common types
-- Common emojis: 👍, ❤️, 😂, 😮, 😢, 🎉, 🔥, 💯

-- Create memory_reactions table
CREATE TABLE IF NOT EXISTS memory_reactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  emoji VARCHAR(10) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(memory_id, user_id, emoji),
  CONSTRAINT valid_emoji CHECK (char_length(emoji) > 0 AND char_length(emoji) <= 10)
);

-- Create memory_comments table (threaded comments)
CREATE TABLE IF NOT EXISTS memory_comments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  parent_comment_id UUID REFERENCES memory_comments(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  deleted_at TIMESTAMPTZ,
  CONSTRAINT valid_content CHECK (char_length(trim(content)) > 0),
  CONSTRAINT no_self_parent CHECK (id != parent_comment_id)
);

-- Create indexes for reactions
CREATE INDEX idx_memory_reactions_memory_id ON memory_reactions(memory_id);
CREATE INDEX idx_memory_reactions_user_id ON memory_reactions(user_id);
CREATE INDEX idx_memory_reactions_created_at ON memory_reactions(created_at);
CREATE INDEX idx_memory_reactions_emoji ON memory_reactions(emoji);

-- Create indexes for comments
CREATE INDEX idx_memory_comments_memory_id ON memory_comments(memory_id);
CREATE INDEX idx_memory_comments_user_id ON memory_comments(user_id);
CREATE INDEX idx_memory_comments_parent_comment_id ON memory_comments(parent_comment_id);
CREATE INDEX idx_memory_comments_created_at ON memory_comments(created_at);
CREATE INDEX idx_memory_comments_deleted_at ON memory_comments(deleted_at) WHERE deleted_at IS NULL;

-- Create composite index for feed ordering (memory_id, created_at)
CREATE INDEX idx_memory_comments_memory_created ON memory_comments(memory_id, created_at) WHERE deleted_at IS NULL;

-- Apply updated_at triggers
CREATE TRIGGER update_memory_reactions_updated_at
  BEFORE UPDATE ON memory_reactions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_comments_updated_at
  BEFORE UPDATE ON memory_comments
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE memory_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_comments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for memory_reactions
CREATE POLICY "Users can view reactions for memories in their family"
  ON memory_reactions FOR SELECT
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

CREATE POLICY "Users can create reactions for memories in their family"
  ON memory_reactions FOR INSERT
  WITH CHECK (
    memory_id IN (
      SELECT id FROM memories
      WHERE family_unit_id IN (
        SELECT family_unit_id 
        FROM user_profiles 
        WHERE id = auth.uid()
      )
    )
    AND user_id = auth.uid()
  );

CREATE POLICY "Users can update their own reactions"
  ON memory_reactions FOR UPDATE
  USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own reactions"
  ON memory_reactions FOR DELETE
  USING (user_id = auth.uid());

-- RLS Policies for memory_comments
CREATE POLICY "Users can view comments for memories in their family"
  ON memory_comments FOR SELECT
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

CREATE POLICY "Users can create comments for memories in their family"
  ON memory_comments FOR INSERT
  WITH CHECK (
    memory_id IN (
      SELECT id FROM memories
      WHERE family_unit_id IN (
        SELECT family_unit_id 
        FROM user_profiles 
        WHERE id = auth.uid()
      )
    )
    AND user_id = auth.uid()
  );

CREATE POLICY "Users can update their own comments"
  ON memory_comments FOR UPDATE
  USING (user_id = auth.uid() AND deleted_at IS NULL);

CREATE POLICY "Users can soft-delete their own comments or adults can delete any in family"
  ON memory_comments FOR UPDATE
  USING (
    (
      user_id = auth.uid()
      OR EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid()
        AND role = 'adult'
        AND family_unit_id IN (
          SELECT family_unit_id FROM memories WHERE id = memory_comments.memory_id
        )
      )
    )
    AND deleted_at IS NULL
  );

