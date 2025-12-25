-- Migration: User Identity Model
-- Purpose: Reference SQL for Supabase schema (managed via Supabase dashboard)
-- Note: This file is for documentation only. Apply changes via Supabase dashboard or migration tools.

-- Create ENUM types
CREATE TYPE user_role AS ENUM (
  'adult',
  'teen',
  'child',
  'grandparent',
  'pet'
);

CREATE TYPE invite_status AS ENUM (
  'pending',
  'accepted',
  'expired',
  'revoked'
);

-- Create family_units table
CREATE TABLE IF NOT EXISTS family_units (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255),
  created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  family_unit_id UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
  role user_role NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}'::jsonb,
  is_family_creator BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT valid_preferences CHECK (jsonb_typeof(preferences) = 'object')
);

-- Create invites table
CREATE TABLE IF NOT EXISTS invites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  family_unit_id UUID NOT NULL REFERENCES family_units(id) ON DELETE CASCADE,
  invited_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  role user_role NOT NULL,
  token VARCHAR(255) UNIQUE NOT NULL,
  status invite_status DEFAULT 'pending',
  expires_at TIMESTAMPTZ NOT NULL,
  accepted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
  CONSTRAINT future_expiration CHECK (expires_at > created_at)
);

-- Create user_sessions table for refresh token storage
CREATE TABLE IF NOT EXISTS user_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  refresh_token_jti VARCHAR(255) UNIQUE NOT NULL,
  device_info JSONB,
  ip_address INET,
  user_agent TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_profiles_family_unit_id ON user_profiles(family_unit_id);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_invites_family_unit_id ON invites(family_unit_id);
CREATE INDEX idx_invites_email ON invites(email);
CREATE INDEX idx_invites_token ON invites(token);
CREATE INDEX idx_invites_status ON invites(status);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_refresh_token_jti ON user_sessions(refresh_token_jti);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_family_units_updated_at
  BEFORE UPDATE ON family_units
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invites_updated_at
  BEFORE UPDATE ON invites
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at
  BEFORE UPDATE ON user_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE family_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for family_units
CREATE POLICY "Users can view their own family unit"
  ON family_units FOR SELECT
  USING (
    id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
  );

CREATE POLICY "First user can create family unit"
  ON family_units FOR INSERT
  WITH CHECK (created_by = auth.uid());

CREATE POLICY "Adults can update their family unit"
  ON family_units FOR UPDATE
  USING (
    id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid() 
      AND role = 'adult'
    )
  );

-- RLS Policies for user_profiles
CREATE POLICY "Users can view profiles in their family"
  ON user_profiles FOR SELECT
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
  );

CREATE POLICY "Users can create their own profile"
  ON user_profiles FOR INSERT
  WITH CHECK (id = auth.uid());

CREATE POLICY "Users can update their own profile"
  ON user_profiles FOR UPDATE
  USING (id = auth.uid());

-- RLS Policies for invites
CREATE POLICY "Users can view invites for their family"
  ON invites FOR SELECT
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid()
    )
    OR email = (SELECT email FROM auth.users WHERE id = auth.uid())
  );

CREATE POLICY "Adults can create invites for their family"
  ON invites FOR INSERT
  WITH CHECK (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid() 
      AND role = 'adult'
    )
  );

CREATE POLICY "Adults can update invites for their family"
  ON invites FOR UPDATE
  USING (
    family_unit_id IN (
      SELECT family_unit_id 
      FROM user_profiles 
      WHERE id = auth.uid() 
      AND role = 'adult'
    )
  );

-- RLS Policies for user_sessions
CREATE POLICY "Users can view their own sessions"
  ON user_sessions FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can create their own sessions"
  ON user_sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own sessions"
  ON user_sessions FOR UPDATE
  USING (user_id = auth.uid());

-- Function to generate invite token
CREATE OR REPLACE FUNCTION generate_invite_token()
RETURNS VARCHAR(255) AS $$
DECLARE
  token VARCHAR(255);
BEGIN
  token := encode(gen_random_bytes(32), 'base64');
  token := replace(token, '/', '_');
  token := replace(token, '+', '-');
  token := replace(token, '=', '');
  RETURN token;
END;
$$ LANGUAGE plpgsql;

-- Function to validate invite token
CREATE OR REPLACE FUNCTION is_invite_valid(invite_token VARCHAR(255))
RETURNS BOOLEAN AS $$
DECLARE
  invite_record RECORD;
BEGIN
  SELECT * INTO invite_record
  FROM invites
  WHERE token = invite_token
    AND status = 'pending';
  
  IF NOT FOUND THEN
    RETURN FALSE;
  END IF;
  
  -- Check expiration
  IF invite_record.expires_at < NOW() THEN
    UPDATE invites
    SET status = 'expired', updated_at = NOW()
    WHERE id = invite_record.id;
    RETURN FALSE;
  END IF;
  
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

