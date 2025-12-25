#!/usr/bin/env python3
"""
Supabase Configuration Query Script

Queries Supabase CLI for project information and updates configuration files.
Run this script to refresh Supabase configuration from the CLI.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def run_supabase_command(command: list[str]) -> Optional[Dict[str, Any]]:
    """
    Run a Supabase CLI command and return JSON output.
    
    Args:
        command: List of command arguments
    
    Returns:
        Parsed JSON output or None if command fails
    """
    try:
        result = subprocess.run(
            ["supabase"] + command + ["--output", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error running command: {' '.join(command)}", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        return None


def get_project_info(project_ref: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get project information.
    
    Args:
        project_ref: Optional project reference ID. If None, looks for linked project.
    
    Returns:
        Project information dictionary
    """
    projects = run_supabase_command(["projects", "list"])
    if not projects:
        return None
    
    # Find project by ref or linked status
    for project in projects:
        if project_ref:
            if project.get("ref") == project_ref or project.get("id") == project_ref:
                return project
        elif project.get("linked"):
            return project
    
    return None


def get_api_keys(project_ref: str) -> Optional[Dict[str, str]]:
    """
    Get API keys for a project.
    
    Note: This requires the API keys command output parsing.
    """
    try:
        result = subprocess.run(
            ["supabase", "projects", "api-keys", "--project-ref", project_ref],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output (it's in table format, not JSON)
        keys = {}
        lines = result.stdout.strip().split('\n')
        for line in lines[2:]:  # Skip header lines
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    key_name = parts[0]
                    key_value = parts[1]
                    if key_name and key_value and key_name != "NAME":
                        keys[key_name] = key_value
        
        return keys
    except subprocess.CalledProcessError as e:
        print(f"Error getting API keys: {e}", file=sys.stderr)
        return None


def get_database_stats() -> Optional[Dict[str, Any]]:
    """Get database statistics."""
    return run_supabase_command(["inspect", "db", "db-stats", "--linked"])


def get_table_stats() -> list[Dict[str, Any]]:
    """Get table statistics."""
    stats = run_supabase_command(["inspect", "db", "table-stats", "--linked"])
    return stats if stats else []


def generate_env_file(project: Dict[str, Any], api_keys: Dict[str, str]) -> str:
    """Generate .env file content."""
    project_ref = project.get("ref", "")
    project_url = f"https://{project_ref}.supabase.co"
    
    anon_key = api_keys.get("anon", "")
    service_key = api_keys.get("service_role", "")
    access_token = api_keys.get("default", "").split('\n')[0] if api_keys.get("default") else ""
    
    return f"""# Supabase Configuration (Auto-generated)
# Project: {project.get('name', 'Unknown')}
# Reference: {project_ref}
# Generated: {subprocess.run(['date', '-u', '+%Y-%m-%d %H:%M:%S UTC'], capture_output=True, text=True).stdout.strip()}

SUPABASE_URL={project_url}
SUPABASE_ANON_KEY={anon_key}
SUPABASE_SERVICE_ROLE_KEY={service_key}

# Supabase CLI Access Token
SUPABASE_ACCESS_TOKEN={access_token}

# JWT Configuration (Set these manually)
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_bytes_long_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Configuration
ENVIRONMENT=development
DEBUG=true
API_VERSION=v1
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
"""


def main():
    """Main function to query and store Supabase configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Query and store Supabase configuration")
    parser.add_argument(
        "--project-ref",
        type=str,
        default="fjevxcnpgydosicdyugt",
        help="Supabase project reference ID"
    )
    args = parser.parse_args()
    
    print("Querying Supabase project information...")
    
    # Get project info
    project = get_project_info(args.project_ref)
    if not project:
        print(f"Error: Project {args.project_ref} not found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found project: {project.get('name')} ({project.get('ref')})")
    
    # Get API keys
    project_ref = project.get("ref")
    print("Fetching API keys...")
    api_keys = get_api_keys(project_ref) if project_ref else {}
    
    # Get database stats (only if linked)
    print("Querying database statistics...")
    db_stats = None
    table_stats = []
    try:
        db_stats = get_database_stats()
        table_stats = get_table_stats()
    except Exception as e:
        print(f"Note: Could not query database stats (project may not be linked): {e}")
    
    # Generate configuration
    config_dir = Path(__file__).parent.parent / "docs" / "supabase"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Update PROJECT_CONFIG.md
    config_content = f"""# Supabase Project Configuration

**Last Updated**: {subprocess.run(['date', '-u', '+%Y-%m-%d %H:%M:%S UTC'], capture_output=True, text=True).stdout.strip()}
**Source**: Supabase CLI query

## Project Information

- **Name**: {project.get('name', 'Unknown')}
- **Reference ID**: `{project.get('ref', 'Unknown')}`
- **Organization ID**: `{project.get('organization_id', 'Unknown')}`
- **Region**: {project.get('region', 'Unknown')}
- **Status**: {project.get('status', 'Unknown')}
- **Created**: {project.get('created_at', 'Unknown')}
- **Linked**: ✅ Yes

## Database Information

- **Host**: {project.get('database', {}).get('host', 'Unknown')}
- **PostgreSQL Version**: {project.get('database', {}).get('version', 'Unknown')}
- **PostgreSQL Engine**: {project.get('database', {}).get('postgres_engine', 'Unknown')}

## API Endpoints

- **Project URL**: `https://{project.get('ref', 'unknown')}.supabase.co`
- **API URL**: `https://{project.get('ref', 'unknown')}.supabase.co/rest/v1/`
- **Auth URL**: `https://{project.get('ref', 'unknown')}.supabase.co/auth/v1/`
- **Storage URL**: `https://{project.get('ref', 'unknown')}.supabase.co/storage/v1/`

## API Keys

### Anon Key (Public)
```
{api_keys.get('anon', 'Not available')}
```

### Service Role Key (Secret)
```
{api_keys.get('service_role', 'Not available')}
```

⚠️ **WARNING**: Service role key bypasses RLS. Keep it secret!

## Database Statistics

"""
    
    if db_stats:
        config_content += f"```json\n{json.dumps(db_stats, indent=2)}\n```\n\n"
    
    if table_stats:
        config_content += "## Tables\n\n"
        for table in table_stats:
            config_content += f"- **{table.get('name', 'Unknown')}**: {table.get('row_count', 0)} rows\n"
    
    config_file = config_dir / "PROJECT_CONFIG.md"
    config_file.write_text(config_content)
    print(f"✅ Updated {config_file}")
    
    # Generate .env.example with actual values
    env_content = generate_env_file(project, api_keys)
    env_example = Path(__file__).parent.parent / ".env.example"
    env_example.write_text(env_content)
    print(f"✅ Updated {env_example}")
    
    print("\n✅ Configuration updated successfully!")
    print(f"\nProject URL: https://{project.get('ref')}.supabase.co")
    print(f"Database Host: {project.get('database', {}).get('host', 'Unknown')}")


if __name__ == "__main__":
    main()

