# Supabase Configuration Documentation

This directory contains Supabase project configuration and database information.

## Files

### PROJECT_CONFIG.md

Complete Supabase project configuration including:
- Project information (name, ID, region, status)
- Database connection details
- API endpoints and keys
- Database statistics (when available)

**Last Updated**: Automatically updated by `scripts/supabase_config.py`

## Updating Configuration

To refresh the Supabase configuration from the CLI:

```bash
python3 scripts/supabase_config.py
```

Or for a specific project:

```bash
python3 scripts/supabase_config.py --project-ref <project-ref>
```

## Environment Variables

The configuration includes all required environment variables for the backend:

- `SUPABASE_URL` - Project API URL
- `SUPABASE_ANON_KEY` - Public anon key (safe for client-side)
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (server-side only, bypasses RLS)
- `SUPABASE_ACCESS_TOKEN` - CLI access token for Supabase operations

See `PROJECT_CONFIG.md` for the complete list and current values.

## Security Notes

⚠️ **Important**: 
- Never commit actual API keys to version control
- Service role key bypasses all Row Level Security policies
- Keep service role key secret and use only server-side
- Anon key is safe for client-side use but requires proper RLS configuration

