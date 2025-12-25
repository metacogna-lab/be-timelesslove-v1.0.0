#!/usr/bin/env python3
"""
Populate test database with required user and family data for testing.

This script creates test users, families, and relationships needed for
authentication and authorization tests.
"""

import asyncio
import os
import sys
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.supabase import get_supabase_service_client
from app.services.user_service import create_user_profile
from app.services.family_service import create_family_unit


async def populate_test_data():
    """Populate test database with seed data."""

    # Test data constants (matching conftest.py fixtures)
    TEST_FAMILY_UNIT_ID = "660e8400-e29b-41d4-a716-446655440001"
    TEST_ADULT_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
    TEST_TEEN_USER_ID = "550e8400-e29b-41d4-a716-446655440002"
    TEST_CHILD_USER_ID = "550e8400-e29b-41d4-a716-446655440003"

    supabase = get_supabase_service_client()

    try:
        print("🌱 Populating test database...")

        # 1. Create test family unit
        print("  📝 Creating test family unit...")
        # Note: created_by references auth.users, so we skip it for testing
        family_data = {
            "id": TEST_FAMILY_UNIT_ID,
            "name": "Test Family"
        }

        try:
            result = supabase.table("family_units").insert(family_data).execute()
            if result.data:
                print("    ✅ Family unit created")
            else:
                print("    ⚠️  Family unit may already exist")
        except Exception as e:
            print(f"    ⚠️  Could not create family unit: {e}")
            print("    Continuing with user creation...")

        # 2. Create test users
        test_users = [
            {
                "id": TEST_ADULT_USER_ID,
                "display_name": "Test Adult",
                "role": "adult",
                "family_unit_id": TEST_FAMILY_UNIT_ID,
                "is_family_creator": True
            },
            {
                "id": TEST_TEEN_USER_ID,
                "display_name": "Test Teen",
                "role": "teen",
                "family_unit_id": TEST_FAMILY_UNIT_ID,
                "is_family_creator": False
            },
            {
                "id": TEST_CHILD_USER_ID,
                "display_name": "Test Child",
                "role": "child",
                "family_unit_id": TEST_FAMILY_UNIT_ID,
                "is_family_creator": False
            }
        ]

        for user_data in test_users:
            print(f"  👤 Creating user: {user_data['display_name']}...")
            result = supabase.table("user_profiles").insert(user_data).execute()
            if result.data:
                print(f"    ✅ {user_data['display_name']} created")
            else:
                print(f"    ⚠️  {user_data['display_name']} may already exist")

        # 3. Create test invitation
        print("  📧 Creating test invitation...")
        invite_data = {
            "id": str(uuid4()),
            "family_unit_id": TEST_FAMILY_UNIT_ID,
            "invited_by": TEST_ADULT_USER_ID,
            "email": "invitee@test.com",
            "role": "teen",
            "token": "valid_token",
            "status": "pending",
            "expires_at": "2025-12-31T23:59:59Z"
        }

        result = supabase.table("invites").insert(invite_data).execute()
        if result.data:
            print("    ✅ Test invitation created")
        else:
            print("    ⚠️  Test invitation may already exist")

        print("✅ Test database populated successfully!")
        print("\nTest data summary:")
        print(f"  Family Unit ID: {TEST_FAMILY_UNIT_ID}")
        print(f"  Adult User ID: {TEST_ADULT_USER_ID}")
        print(f"  Teen User ID: {TEST_TEEN_USER_ID}")
        print(f"  Child User ID: {TEST_CHILD_USER_ID}")
        print("  Invitation Token: valid_token")

    except Exception as e:
        print(f"❌ Error populating test data: {e}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(populate_test_data())
    sys.exit(0 if success else 1)