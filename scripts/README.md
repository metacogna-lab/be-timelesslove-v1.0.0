# Backend Scripts

Utility scripts for managing the Timeless Love backend.

## supabase_config.py

Queries Supabase CLI for project information and updates configuration files.

### Usage

```bash
# Query and update configuration for the default project
python3 scripts/supabase_config.py

# Query a specific project
python3 scripts/supabase_config.py --project-ref fjevxcnpgydosicdyugt
```

### What It Does

1. Queries Supabase CLI for project information
2. Fetches API keys (anon and service_role)
3. Updates `docs/supabase/PROJECT_CONFIG.md` with project details
4. Updates `.env.example` with actual Supabase credentials

### Requirements

- Supabase CLI installed and authenticated
- Project must be accessible via CLI (either linked or by project-ref)
- Valid Supabase access token in environment or CLI config

### Output Files

- `docs/supabase/PROJECT_CONFIG.md` - Complete project configuration documentation
- `.env.example` - Environment variable template with actual Supabase values

### Notes

- The script does not overwrite your actual `.env` file (only `.env.example`)
- API keys are fetched from the Supabase CLI
- Database statistics are only available if the project is properly linked

