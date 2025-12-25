#!/usr/bin/env python3
"""
Apply all Supabase setup: Create bucket and apply migrations via SQL Editor instructions.
This script provides a comprehensive setup guide and attempts automated steps where possible.
"""

import sys
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.db.supabase import get_supabase_service_client
    from app.config import get_settings
    from supabase import Client
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure dependencies are installed: pip install supabase requests")
    sys.exit(1)


def create_storage_bucket_via_api(bucket_name: str, public: bool = False) -> bool:
    """Create storage bucket using Supabase REST API."""
    try:
        settings = get_settings()
        
        # Check if bucket exists first
        url = f"{settings.supabase_url}/storage/v1/bucket"
        headers = {
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
            "Content-Type": "application/json"
        }
        
        # List existing buckets
        list_url = f"{settings.supabase_url}/storage/v1/bucket"
        list_req = Request(list_url, headers=headers)
        
        try:
            with urlopen(list_req) as response:
                if response.status == 200:
                    buckets = json.loads(response.read())
                    existing_names = [b.get('name') for b in buckets if isinstance(b, dict)]
                    if bucket_name in existing_names:
                        print(f"✓ Bucket '{bucket_name}' already exists")
                        return True
        except HTTPError as e:
            if e.code != 404:
                print(f"⚠️  Could not check existing buckets: {e}")
        
        # Create bucket
        data = {
            "name": bucket_name,
            "public": public,
            "file_size_limit": 52428800,  # 50MB
            "allowed_mime_types": [
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "video/mp4",
                "video/webm"
            ]
        }
        
        req = Request(url, data=json.dumps(data).encode(), headers=headers, method='POST')
        
        try:
            with urlopen(req) as response:
                if response.status in [200, 201]:
                    print(f"✓ Successfully created bucket '{bucket_name}'")
                    return True
        except HTTPError as e:
            if e.code == 409:
                print(f"✓ Bucket '{bucket_name}' already exists")
                return True
            else:
                print(f"✗ Failed to create bucket: {e.code}")
                error_body = e.read().decode() if hasattr(e, 'read') else str(e)
                print(f"  Response: {error_body}")
                return False
            
    except Exception as e:
        print(f"✗ Error creating bucket: {e}")
        return False


def read_migration_files() -> dict:
    """Read all migration files."""
    migrations_dir = backend_dir / "db" / "migrations"
    migrations = {}
    
    if not migrations_dir.exists():
        return migrations
    
    for migration_file in sorted(migrations_dir.glob("*.sql")):
        try:
            with open(migration_file, 'r') as f:
                migrations[migration_file.name] = f.read()
        except Exception as e:
            print(f"⚠️  Error reading {migration_file.name}: {e}")
    
    return migrations


def apply_migration_via_api(migration_name: str, sql: str) -> bool:
    """Attempt to apply migration via Supabase REST API (limited support)."""
    # Note: Supabase REST API doesn't support arbitrary SQL execution
    # This would require using the Management API or direct database connection
    # For now, we'll provide instructions
    return False


def main():
    """Main setup function."""
    print("="*60)
    print("Supabase Setup: Bucket & Migrations")
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
        print("  Make sure backend/.env is configured")
        return False
    
    # Create storage bucket
    print("="*60)
    print("Step 1: Creating Storage Bucket")
    print("="*60)
    print()
    
    bucket_created = create_storage_bucket_via_api("memories", public=False)
    
    if not bucket_created:
        print("\n⚠️  Automated bucket creation failed.")
        print("   Manual creation required:")
        print("   1. Go to: https://supabase.com/dashboard/project/fjevxcnpgydosicdyugt")
        print("   2. Navigate to: Storage > Buckets")
        print("   3. Click 'New bucket'")
        print("   4. Name: memories")
        print("   5. Public: No")
        print("   6. File size limit: 50MB")
        print("   7. Click 'Create bucket'")
    
    print()
    
    # Prepare migrations
    print("="*60)
    print("Step 2: Database Migrations")
    print("="*60)
    print()
    
    migrations = read_migration_files()
    
    if not migrations:
        print("✗ No migration files found in backend/db/migrations/")
        return False
    
    print(f"✓ Found {len(migrations)} migration file(s):")
    for name in sorted(migrations.keys()):
        print(f"   - {name}")
    
    print()
    print("⚠️  Migrations must be applied manually via Supabase Dashboard:")
    print()
    print("   1. Open: https://supabase.com/dashboard/project/fjevxcnpgydosicdyugt")
    print("   2. Go to: SQL Editor")
    print("   3. Apply each migration in order:")
    print()
    
    for i, (name, sql) in enumerate(sorted(migrations.items()), 1):
        print(f"   Migration {i}: {name}")
        print(f"   - Copy contents from: backend/db/migrations/{name}")
        print(f"   - Paste into SQL Editor")
        print(f"   - Click 'Run'")
        print()
    
    # Create combined migration file for convenience
    combined_path = backend_dir / "db" / "migrations" / "_combined_all_migrations.sql"
    try:
        with open(combined_path, 'w') as f:
            f.write("-- Combined Migration for Timeless Love\n")
            f.write("-- Generated automatically - Apply via Supabase SQL Editor\n")
            f.write("-- Source: Individual migration files in this directory\n\n")
            
            for name, sql in sorted(migrations.items()):
                f.write(f"-- {'='*60}\n")
                f.write(f"-- Migration: {name}\n")
                f.write(f"-- {'='*60}\n\n")
                f.write(sql)
                f.write("\n\n")
        
        print(f"✓ Combined migration file created: {combined_path}")
        print("   You can copy this entire file to SQL Editor for convenience")
        print()
    except Exception as e:
        print(f"⚠️  Could not create combined file: {e}")
        print()
    
    # Summary
    print("="*60)
    print("Setup Summary")
    print("="*60)
    print()
    
    if bucket_created:
        print("✓ Storage bucket 'memories': Created")
    else:
        print("⚠️  Storage bucket 'memories': Manual creation required")
    
    print("⚠️  Database migrations: Manual application required")
    print()
    
    print("Next Steps:")
    print("1. Verify bucket exists in Supabase Dashboard > Storage")
    print("2. Apply migrations in Supabase Dashboard > SQL Editor")
    print("3. Verify tables using verification queries")
    print("4. Test backend connection")
    print()
    
    return bucket_created


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

