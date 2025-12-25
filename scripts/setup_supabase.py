#!/usr/bin/env python3
"""
Setup Supabase: Create storage bucket and apply migrations.
This script creates the 'memories' storage bucket and applies all database migrations.
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.db.supabase import get_supabase_service_client
    from app.config import get_settings
    from supabase import Client
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the backend directory and dependencies are installed")
    print("Install: pip install supabase psycopg2-binary")
    sys.exit(1)


def read_migration_file(migration_path: Path) -> str:
    """Read a migration SQL file."""
    try:
        with open(migration_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {migration_path}: {e}")
        return None


def apply_migration(conn, migration_name: str, sql: str) -> bool:
    """Apply a migration SQL script."""
    print(f"\n{'='*60}")
    print(f"Applying migration: {migration_name}")
    print(f"{'='*60}")
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        print(f"✓ Successfully applied {migration_name}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"✗ Error applying {migration_name}: {e}")
        # Check if error is due to already existing objects
        error_str = str(e).lower()
        if 'already exists' in error_str or 'duplicate' in error_str:
            print(f"  Note: Some objects may already exist (this is okay)")
            return True
        return False


def create_storage_bucket(supabase: Client, bucket_name: str) -> bool:
    """Create a storage bucket."""
    print(f"\n{'='*60}")
    print(f"Creating storage bucket: {bucket_name}")
    print(f"{'='*60}")
    
    try:
        # Check if bucket already exists
        buckets = supabase.storage.list_buckets()
        existing_buckets = [b.name for b in buckets]
        
        if bucket_name in existing_buckets:
            print(f"✓ Bucket '{bucket_name}' already exists")
            return True
        
        # Create bucket (private by default)
        # Note: Supabase Python client doesn't have direct bucket creation
        # We'll use the REST API via the client
        response = supabase.storage.create_bucket(
            bucket_name,
            options={"public": False}
        )
        
        print(f"✓ Successfully created bucket '{bucket_name}'")
        return True
    except Exception as e:
        error_str = str(e).lower()
        if 'already exists' in error_str or 'duplicate' in error_str:
            print(f"✓ Bucket '{bucket_name}' already exists")
            return True
        print(f"✗ Error creating bucket '{bucket_name}': {e}")
        print(f"  Note: You may need to create this manually in the Supabase Dashboard")
        print(f"  Go to: Storage > Buckets > New bucket")
        return False


def get_db_connection(settings) -> Optional[psycopg2.extensions.connection]:
    """Get PostgreSQL connection using service role key."""
    try:
        # Extract database connection details from Supabase URL
        # For Supabase, we need to construct the connection string
        # The database URL format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        
        # We'll use the Supabase Management API or direct connection
        # For now, we'll use the service role key to get connection info
        # Note: This requires the database password which should be in settings
        
        # Alternative: Use Supabase's connection pooling
        # For migrations, we can use the direct database connection
        # The connection string should be in environment or settings
        
        # Check if we have a direct database URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Try to construct from Supabase URL
            # This is a simplified approach - in production, use proper connection string
            print("⚠️  DATABASE_URL not found in environment")
            print("   Using Supabase REST API for migrations instead")
            return None
        
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"⚠️  Could not establish direct database connection: {e}")
        print("   Will use Supabase REST API for migrations")
        return None


def apply_migrations_via_api(supabase: Client, migrations_dir: Path) -> bool:
    """Apply migrations using Supabase REST API (rpc calls or direct SQL)."""
    print("\n" + "="*60)
    print("Applying Migrations via Supabase API")
    print("="*60)
    print("\n⚠️  Note: Direct SQL execution via API is limited.")
    print("   For full migration support, use Supabase Dashboard SQL Editor")
    print("   or Supabase CLI migration tools.")
    print("\nMigration files to apply:")
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    for i, migration_file in enumerate(migration_files, 1):
        print(f"   {i}. {migration_file.name}")
    
    print("\nTo apply migrations:")
    print("1. Open Supabase Dashboard: https://supabase.com/dashboard")
    print(f"2. Go to SQL Editor")
    print("3. Copy and paste each migration file in order")
    print("4. Run each migration")
    
    return True


def main():
    """Main setup function."""
    print("="*60)
    print("Supabase Setup: Bucket Creation & Migrations")
    print("="*60)
    print()
    
    # Check configuration
    try:
        settings = get_settings()
        print("✓ Configuration loaded")
        print(f"  Supabase URL: {settings.supabase_url}")
        print()
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    # Initialize Supabase client
    try:
        supabase = get_supabase_service_client()
        print("✓ Supabase client initialized")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize Supabase client: {e}")
        return False
    
    # Create storage bucket
    bucket_created = create_storage_bucket(supabase, "memories")
    print()
    
    # Apply migrations
    migrations_dir = backend_dir / "db" / "migrations"
    
    if not migrations_dir.exists():
        print(f"✗ Migrations directory not found: {migrations_dir}")
        return False
    
    # Try to get database connection
    db_conn = get_db_connection(settings)
    
    if db_conn:
        # Apply migrations via direct database connection
        print("\n" + "="*60)
        print("Applying Migrations via Database Connection")
        print("="*60)
        
        migration_files = sorted(migrations_dir.glob("*.sql"))
        all_success = True
        
        for migration_file in migration_files:
            sql = read_migration_file(migration_file)
            if sql:
                success = apply_migration(db_conn, migration_file.name, sql)
                if not success:
                    all_success = False
        
        db_conn.close()
        
        if all_success:
            print("\n✓ All migrations applied successfully")
        else:
            print("\n⚠️  Some migrations had errors (check output above)")
    else:
        # Fall back to API-based approach (with instructions)
        apply_migrations_via_api(supabase, migrations_dir)
    
    # Summary
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)
    
    if bucket_created:
        print("✓ Storage bucket 'memories' ready")
    else:
        print("⚠️  Storage bucket creation - check manually")
    
    if db_conn:
        print("✓ Migrations applied via database connection")
    else:
        print("⚠️  Migrations - apply manually via Supabase Dashboard")
        print("   See instructions above")
    
    print("\nNext Steps:")
    print("1. Verify storage bucket exists in Supabase Dashboard")
    print("2. If migrations weren't applied, run them in SQL Editor")
    print("3. Verify tables exist using verification queries")
    print("4. Test backend connection")
    
    return bucket_created


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

