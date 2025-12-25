#!/usr/bin/env python3
"""
Create Supabase storage bucket.
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
    print("Make sure dependencies are installed: pip install supabase")
    sys.exit(1)


def create_bucket(bucket_name: str, public: bool = False) -> bool:
    """Create a storage bucket."""
    try:
        settings = get_settings()
        supabase = get_supabase_service_client()
        
        # Check if bucket already exists
        try:
            buckets = supabase.storage.list_buckets()
            existing_buckets = [b.name for b in buckets]
            
            if bucket_name in existing_buckets:
                print(f"✓ Bucket '{bucket_name}' already exists")
                return True
        except Exception as e:
            print(f"⚠️  Could not list buckets: {e}")
        
        # Try to create bucket using REST API
        # Note: Supabase Python client may not have direct bucket creation
        # We'll use the storage API endpoint directly
        
        try:
            # Use the storage API to create bucket
            response = supabase.storage.create_bucket(
                bucket_name,
                options={"public": public}
            )
            print(f"✓ Successfully created bucket '{bucket_name}'")
            return True
        except AttributeError:
            # If create_bucket doesn't exist, use REST API directly
            import requests
            
            url = f"{settings.supabase_url}/storage/v1/bucket"
            headers = {
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "apikey": settings.supabase_service_role_key,
                "Content-Type": "application/json"
            }
            data = {
                "name": bucket_name,
                "public": public
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"✓ Successfully created bucket '{bucket_name}'")
                return True
            elif response.status_code == 409:
                print(f"✓ Bucket '{bucket_name}' already exists")
                return True
            else:
                print(f"✗ Failed to create bucket: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"✗ Error creating bucket '{bucket_name}': {e}")
        print(f"  Note: You may need to create this manually in Supabase Dashboard")
        print(f"  Go to: Storage > Buckets > New bucket")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_bucket.py <bucket_name> [public]")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    public = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else False
    
    success = create_bucket(bucket_name, public)
    sys.exit(0 if success else 1)

