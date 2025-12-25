#!/usr/bin/env python3
"""
Verify Supabase setup and readiness.
Checks database tables, storage buckets, and configuration.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.db.supabase import get_supabase_service_client
    from app.config import get_settings
    from supabase import Client
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the backend directory and dependencies are installed")
    sys.exit(1)


def check_database_tables(supabase: Client) -> dict:
    """Check if required database tables exist."""
    required_tables = [
        'family_units',
        'user_profiles',
        'invites',
        'user_sessions',
        'memories',
        'memory_media',
        'memory_reactions',
        'memory_comments',
        'analytics_events',
        'analytics_metrics'
    ]
    
    results = {}
    
    for table in required_tables:
        try:
            # Try to query the table (limit 0 to just check existence)
            result = supabase.table(table).select('*', count='exact').limit(0).execute()
            results[table] = {
                'exists': True,
                'count': result.count if hasattr(result, 'count') else 'unknown'
            }
        except Exception as e:
            results[table] = {
                'exists': False,
                'error': str(e)
            }
    
    return results


def check_storage_buckets(supabase: Client) -> dict:
    """Check if required storage buckets exist."""
    required_bucket = 'memories'
    
    try:
        # List buckets
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        return {
            'memories': {
                'exists': required_bucket in bucket_names,
                'all_buckets': bucket_names
            }
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def check_enums(supabase: Client) -> dict:
    """Check if required ENUM types exist."""
    required_enums = [
        'user_role',
        'invite_status',
        'memory_status',
        'processing_status'
    ]
    
    # Note: Checking ENUMs requires direct SQL query
    # For now, we'll check if tables using these ENUMs exist
    return {
        'note': 'ENUM verification requires SQL query - checking via table existence'
    }


def main():
    """Main verification function."""
    print("=" * 60)
    print("Supabase Readiness Verification")
    print("=" * 60)
    print()
    
    # Check configuration
    try:
        settings = get_settings()
        print("✓ Configuration loaded")
        print(f"  Supabase URL: {settings.supabase_url}")
        print(f"  API Version: {settings.api_version}")
        print()
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    # Check database connection
    try:
        supabase = get_supabase_service_client()
        print("✓ Supabase client initialized")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize Supabase client: {e}")
        return False
    
    # Check database tables
    print("Checking database tables...")
    table_results = check_database_tables(supabase)
    
    all_tables_exist = True
    for table, result in table_results.items():
        if result.get('exists'):
            count = result.get('count', '?')
            print(f"  ✓ {table} exists (count: {count})")
        else:
            print(f"  ✗ {table} missing: {result.get('error', 'Unknown error')}")
            all_tables_exist = False
    
    print()
    
    # Check storage buckets
    print("Checking storage buckets...")
    bucket_results = check_storage_buckets(supabase)
    
    if 'error' in bucket_results:
        print(f"  ✗ Error checking buckets: {bucket_results['error']}")
    else:
        if bucket_results.get('memories', {}).get('exists'):
            print("  ✓ 'memories' bucket exists")
        else:
            print("  ✗ 'memories' bucket missing")
            print(f"    Available buckets: {bucket_results.get('memories', {}).get('all_buckets', [])}")
    
    print()
    
    # Summary
    print("=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    if all_tables_exist:
        print("✓ All required database tables exist")
    else:
        print("✗ Some database tables are missing")
        print("  Action: Run migrations via Supabase dashboard or CLI")
    
    if bucket_results.get('memories', {}).get('exists'):
        print("✓ Storage bucket 'memories' exists")
    else:
        print("✗ Storage bucket 'memories' missing")
        print("  Action: Create 'memories' bucket in Supabase Storage")
    
    print()
    print("Next Steps:")
    print("1. If tables are missing, apply migrations from backend/db/migrations/")
    print("2. If bucket is missing, create 'memories' bucket in Supabase Storage")
    print("3. Configure RLS policies as documented in migration files")
    print("4. Verify CORS settings allow requests from app.timelesslove.ai")
    
    return all_tables_exist and bucket_results.get('memories', {}).get('exists', False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

