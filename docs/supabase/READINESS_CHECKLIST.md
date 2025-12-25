# Supabase Readiness Checklist

## Project Status

**Project Name**: TimelessLove  
**Reference ID**: `fjevxcnpgydosicdyugt`  
**Status**: ACTIVE_HEALTHY  
**Region**: Southeast Asia (Singapore)

## Verification Steps

### 1. Project Connection

```bash
# Check project status
supabase projects list

# Link project (if not already linked)
supabase link --project-ref fjevxcnpgydosicdyugt
```

**Expected**: Project should appear in list with ACTIVE_HEALTHY status.

### 2. Database Tables

Required tables (from migrations):

#### Phase 1 - User Identity
- [ ] `family_units`
- [ ] `user_profiles`
- [ ] `invites`
- [ ] `user_sessions`

#### Phase 3 - Memories
- [ ] `memories`
- [ ] `memory_media`

#### Phase 4 - Feed Interactions
- [ ] `memory_reactions`
- [ ] `memory_comments`

#### Phase 6 - Analytics
- [ ] `analytics_events`
- [ ] `analytics_metrics`

**Verification**:
```sql
-- Run in Supabase SQL Editor
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'family_units', 'user_profiles', 'invites', 'user_sessions',
    'memories', 'memory_media', 'memory_reactions', 'memory_comments',
    'analytics_events', 'analytics_metrics'
  )
ORDER BY table_name;
```

### 3. ENUM Types

Required ENUM types:

- [ ] `user_role` (adult, teen, child, grandparent, pet)
- [ ] `invite_status` (pending, accepted, expired, revoked)
- [ ] `memory_status` (draft, published, archived)
- [ ] `processing_status` (pending, processing, completed, failed)

**Verification**:
```sql
SELECT typname 
FROM pg_type 
WHERE typname IN ('user_role', 'invite_status', 'memory_status', 'processing_status');
```

### 4. Database Functions

Required functions:

- [ ] `update_updated_at_column()` - Trigger function for updated_at timestamps

**Verification**:
```sql
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
  AND routine_name = 'update_updated_at_column';
```

### 5. Row Level Security (RLS)

All tables should have RLS enabled:

- [ ] `family_units` - RLS enabled
- [ ] `user_profiles` - RLS enabled
- [ ] `invites` - RLS enabled
- [ ] `user_sessions` - RLS enabled
- [ ] `memories` - RLS enabled
- [ ] `memory_media` - RLS enabled
- [ ] `memory_reactions` - RLS enabled
- [ ] `memory_comments` - RLS enabled
- [ ] `analytics_events` - RLS enabled
- [ ] `analytics_metrics` - RLS enabled

**Verification**:
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN (
    'family_units', 'user_profiles', 'invites', 'user_sessions',
    'memories', 'memory_media', 'memory_reactions', 'memory_comments',
    'analytics_events', 'analytics_metrics'
  );
```

### 6. Storage Buckets

Required storage bucket:

- [ ] `memories` - For storing memory media files

**Verification**:
```bash
# Via Supabase Dashboard: Storage > Buckets
# Or via API
```

**Bucket Configuration**:
- **Public**: No (private bucket)
- **File size limit**: 50MB per file
- **Allowed MIME types**: 
  - Images: image/jpeg, image/png, image/gif, image/webp
  - Videos: video/mp4, video/webm

### 7. Indexes

Key indexes should exist for performance:

**User Identity**:
- [ ] `idx_user_profiles_family_unit_id`
- [ ] `idx_user_profiles_role`
- [ ] `idx_invites_family_unit_id`
- [ ] `idx_invites_token`
- [ ] `idx_user_sessions_user_id`

**Memories**:
- [ ] `idx_memories_family_unit_id`
- [ ] `idx_memories_user_id`
- [ ] `idx_memories_created_at`
- [ ] `idx_memories_status`
- [ ] `idx_memory_media_memory_id`

**Feed**:
- [ ] `idx_memory_reactions_memory_id`
- [ ] `idx_memory_comments_memory_id`
- [ ] `idx_memory_comments_parent_comment_id`

**Analytics**:
- [ ] `idx_analytics_events_event_type`
- [ ] `idx_analytics_events_timestamp`
- [ ] `idx_analytics_events_user_id`

**Verification**:
```sql
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

### 8. API Keys

Required keys configured in backend:

- [ ] `SUPABASE_URL` - Project URL
- [ ] `SUPABASE_ANON_KEY` - Public anon key
- [ ] `SUPABASE_SERVICE_ROLE_KEY` - Service role key (for admin operations)

**Location**: `backend/.env`

### 9. CORS Configuration

Backend CORS should allow:

- [ ] `https://app.timelesslove.ai` (production)
- [ ] `http://localhost:5173` (development)
- [ ] `http://localhost:3000` (development)

**Configuration**: `backend/app/config.py` - `CORS_ORIGINS`

### 10. Authentication

Supabase Auth should be:

- [ ] Enabled
- [ ] Email/Password provider enabled
- [ ] Email confirmation: Optional (for development) or Required (for production)

## Quick Verification Script

Run this SQL in Supabase SQL Editor to check all tables:

```sql
-- Check all required tables
WITH required_tables AS (
  SELECT unnest(ARRAY[
    'family_units', 'user_profiles', 'invites', 'user_sessions',
    'memories', 'memory_media', 'memory_reactions', 'memory_comments',
    'analytics_events', 'analytics_metrics'
  ]) AS table_name
)
SELECT 
  rt.table_name,
  CASE 
    WHEN t.table_name IS NOT NULL THEN '✓ EXISTS'
    ELSE '✗ MISSING'
  END AS status,
  CASE 
    WHEN t.rowsecurity THEN 'RLS Enabled'
    ELSE 'RLS Disabled'
  END AS rls_status
FROM required_tables rt
LEFT JOIN pg_tables t ON t.tablename = rt.table_name AND t.schemaname = 'public'
ORDER BY rt.table_name;
```

## Migration Application

To apply migrations:

1. **Via Supabase Dashboard**:
   - Go to SQL Editor
   - Copy contents of migration files from `backend/db/migrations/`
   - Run in order: 001, 002, 003, 004

2. **Via Supabase CLI** (if linked):
   ```bash
   supabase db push
   ```

3. **Manual Application**:
   - Copy SQL from migration files
   - Run in Supabase SQL Editor

## Storage Bucket Setup

1. **Create Bucket**:
   - Go to Storage > Buckets
   - Create new bucket: `memories`
   - Set as private (not public)

2. **Configure Policies**:
   - Users can upload to their family's folder
   - Users can access media in their family
   - Policies enforced via backend signed URLs

## Next Steps After Verification

1. ✅ All tables exist
2. ✅ RLS policies enabled
3. ✅ Storage bucket created
4. ✅ Indexes created
5. ✅ Environment variables configured
6. ✅ CORS configured
7. ✅ Test backend connection
8. ✅ Test authentication flow
9. ✅ Test memory creation
10. ✅ Test feed interactions

## Troubleshooting

### Tables Missing
- Apply migrations from `backend/db/migrations/`
- Check SQL Editor for errors
- Verify user has CREATE TABLE permissions

### RLS Not Enabled
- Enable via: `ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;`
- Create policies as documented in migration files

### Storage Bucket Missing
- Create via Supabase Dashboard: Storage > Buckets
- Configure policies for family-scoped access

### Connection Issues
- Verify API keys in `.env`
- Check Supabase project status
- Verify network connectivity

