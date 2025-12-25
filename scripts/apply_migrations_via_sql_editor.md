# Apply Migrations via Supabase SQL Editor

## Quick Steps

1. **Open Supabase Dashboard**
   - URL: https://supabase.com/dashboard/project/fjevxcnpgydosicdyugt
   - Navigate to: **SQL Editor** (left sidebar)

2. **Copy Combined Migration**
   - Open file: `backend/db/migrations/_combined_all_migrations.sql`
   - Copy **entire contents** (Ctrl+A, Ctrl+C / Cmd+A, Cmd+C)

3. **Paste and Run**
   - Paste into SQL Editor
   - Click **Run** button (or press Ctrl+Enter / Cmd+Enter)
   - Wait for execution to complete

4. **Verify Success**
   - Check for any errors in the output
   - Run verification query (see below)

## Verification Query

After applying migrations, run this in SQL Editor to verify all tables exist:

```sql
SELECT 
  table_name,
  CASE WHEN EXISTS (
    SELECT 1 FROM pg_tables 
    WHERE tablename = table_name AND schemaname = 'public'
  ) THEN '✓ EXISTS' ELSE '✗ MISSING' END AS status
FROM (VALUES 
  ('family_units'), ('user_profiles'), ('invites'), ('user_sessions'),
  ('memories'), ('memory_media'), ('memory_reactions'), ('memory_comments'),
  ('analytics_events'), ('analytics_metrics')
) AS t(table_name)
ORDER BY table_name;
```

Expected result: All tables should show "✓ EXISTS"

## Alternative: Apply Individual Migrations

If you prefer to apply migrations one at a time:

1. **001_user_identity.sql** - User and family tables
2. **002_memories.sql** - Memory and media tables  
3. **003_reactions_comments.sql** - Reactions and comments tables
4. **004_analytics.sql** - Analytics events and metrics tables

Apply in order, waiting for each to complete before proceeding.

## Troubleshooting

### Error: "relation already exists"
- Some tables may already exist - this is okay
- The migration uses `CREATE TABLE IF NOT EXISTS` to handle this

### Error: "type already exists"
- ENUM types may already exist - this is okay
- The migration will skip existing types

### Error: "policy already exists"
- RLS policies may already exist
- You may need to drop existing policies first, or modify the migration

### Connection Issues
- Ensure you're logged into Supabase Dashboard
- Check project is active and accessible

## Next Steps After Migrations

1. ✅ Verify all tables exist (use verification query above)
2. ✅ Verify storage bucket 'memories' exists
3. ✅ Test backend connection
4. ✅ Run backend tests

