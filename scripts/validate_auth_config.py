#!/usr/bin/env python3
"""
Quick validation script for auth and database configuration.
Tests imports and basic functionality without full pytest infrastructure.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all new modules can be imported."""
    print("🧪 Testing Imports...")

    try:
        from app.dependencies.supabase_auth import (
            verify_supabase_token,
            optional_supabase_token,
            SupabaseUser,
            SupabaseJWTVerifier,
        )
        print("  ✓ Supabase auth module imports successfully")
    except Exception as e:
        print(f"  ✗ Supabase auth import failed: {e}")
        return False

    try:
        from app.db.graph_db import (
            get_db_url,
            get_connection_pool,
            init_checkpointer,
            get_checkpointer,
            close_pool,
            get_graph_checkpointer,
        )
        print("  ✓ Graph DB module imports successfully")
    except Exception as e:
        print(f"  ✗ Graph DB import failed: {e}")
        return False

    try:
        from app.config import get_settings
        settings = get_settings()
        print(f"  ✓ Config loaded (Debug: {settings.is_debug})")
    except Exception as e:
        print(f"  ✗ Config import failed: {e}")
        return False

    return True


def test_supabase_user_model():
    """Test SupabaseUser model creation."""
    print("\n🧪 Testing SupabaseUser Model...")

    try:
        from app.dependencies.supabase_auth import SupabaseUser

        # Test with all fields
        user = SupabaseUser(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            role="authenticated",
            app_metadata={"provider": "email"},
            user_metadata={"display_name": "Test User"},
            aud="authenticated",
            family_unit_id="660e8400-e29b-41d4-a716-446655440001",
            user_role="adult",
        )

        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email == "test@example.com"
        assert user.family_unit_id == "660e8400-e29b-41d4-a716-446655440001"
        assert user.user_role == "adult"

        print("  ✓ SupabaseUser model creation works")

        # Test with minimal fields
        minimal_user = SupabaseUser(id="test-id-123")
        assert minimal_user.id == "test-id-123"
        assert minimal_user.email is None
        assert minimal_user.aud == "authenticated"  # Default value

        print("  ✓ SupabaseUser minimal creation works")
        return True

    except Exception as e:
        print(f"  ✗ SupabaseUser model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jwt_verification():
    """Test JWT token creation and verification."""
    print("\n🧪 Testing JWT Verification...")

    try:
        from datetime import datetime, timedelta
        from jose import jwt
        from app.dependencies.supabase_auth import SupabaseJWTVerifier
        from app.utils.jwt import get_jwt_config

        config = get_jwt_config()
        verifier = SupabaseJWTVerifier()

        # Create a valid token
        now = datetime.utcnow()
        payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
            "user_role": "adult",
        }

        token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)
        print(f"  ✓ JWT token created: {token[:50]}...")

        # Verify token
        decoded = verifier.verify_token(token)
        assert decoded["sub"] == "550e8400-e29b-41d4-a716-446655440000"
        assert decoded["email"] == "test@example.com"
        assert decoded["user_role"] == "adult"

        print("  ✓ JWT verification works")

        # Test expired token detection
        expired_payload = {
            "sub": "test-id",
            "aud": "authenticated",
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        }
        expired_token = jwt.encode(expired_payload, config.secret_key, algorithm=config.algorithm)

        try:
            verifier.verify_token(expired_token)
            print("  ✗ Expired token should have been rejected")
            return False
        except Exception:
            print("  ✓ Expired tokens are correctly rejected")

        return True

    except Exception as e:
        print(f"  ✗ JWT verification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_db_url_construction():
    """Test database URL construction."""
    print("\n🧪 Testing Database URL Construction...")

    try:
        from app.db.graph_db import get_db_url

        # Check if SUPABASE_DB_URL is set
        if os.getenv("SUPABASE_DB_URL"):
            url = get_db_url()
            print(f"  ✓ Database URL loaded from env: {url[:50]}...")
            return True
        else:
            print("  ⚠️  SUPABASE_DB_URL not set in environment")
            print("     This is OK - checkpointer will degrade gracefully")
            return True

    except ValueError as e:
        # Missing config is expected if env vars not set
        print(f"  ⚠️  Database URL construction requires SUPABASE_DB_URL or SUPABASE_DB_PASSWORD")
        print("     This is OK for testing - checkpointer will degrade gracefully")
        return True
    except Exception as e:
        print(f"  ✗ Database URL test failed unexpectedly: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_updates():
    """Test that config was updated with new fields."""
    print("\n🧪 Testing Config Updates...")

    try:
        from app.config import Settings

        # Check that new fields exist
        import inspect
        fields = {name for name, _ in inspect.getmembers(Settings) if not name.startswith('_')}

        assert 'supabase_db_url' in fields, "Missing supabase_db_url field"
        assert 'supabase_db_password' in fields, "Missing supabase_db_password field"

        print("  ✓ Config has new database fields")
        return True

    except Exception as e:
        print(f"  ✗ Config update test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Auth & Database Configuration Validation")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("SupabaseUser Model", test_supabase_user_model()))
    results.append(("JWT Verification", test_jwt_verification()))
    results.append(("Database URL", test_db_url_construction()))
    results.append(("Config Updates", test_config_updates()))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All validation tests passed!")
        print("\nNext steps:")
        print("  1. Install full dependencies: pip install -r requirements.txt")
        print("  2. Run full test suite: pytest tests/test_supabase_auth.py -v")
        print("  3. Update .env with SUPABASE_DB_URL")
        print("  4. Add startup/shutdown events to app/main.py")
        return 0
    else:
        print("\n❌ Some validation tests failed")
        print("Review the errors above and ensure all dependencies are installed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
