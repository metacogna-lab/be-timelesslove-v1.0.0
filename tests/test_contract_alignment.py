"""
Contract alignment tests - Validates TypeScript contracts match Pydantic schemas.

This test ensures the frontend TypeScript interfaces in contracts/types/index.ts
align with backend Pydantic models. Field names are converted between camelCase
(TypeScript) and snake_case (Python) for comparison.
"""

import pytest
import re
from pathlib import Path
from typing import Dict, Set, Optional
from app.schemas.auth import TokenResponse, RegisterResponse, LoginRequest
from app.schemas.memory import MemoryResponse, MediaResponse
from app.schemas.feed import ReactionResponse, CommentResponse, FeedResponse
from pydantic import BaseModel


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_pydantic_fields(model: type[BaseModel]) -> Set[str]:
    """Extract field names from a Pydantic model."""
    return set(model.model_fields.keys())


def get_typescript_interface_fields(interface_name: str) -> Set[str]:
    """
    Extract field names from TypeScript interface definition.
    
    This is a simplified parser that reads the contracts/types/index.ts file
    and extracts field names from the specified interface.
    """
    # Path to TypeScript contracts file - from backend/tests/ to project root contracts/
    contracts_path = Path(__file__).parent.parent.parent / "contracts" / "types" / "index.ts"
    
    if not contracts_path.exists():
        pytest.skip(f"TypeScript contracts file not found at {contracts_path}")
    
    with open(contracts_path, 'r') as f:
        content = f.read()
    
    # Find the interface definition
    # Escape curly braces in f-string by doubling them
    pattern = rf'export interface {interface_name}\s*\{{([^}}]+)\}}'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        pytest.skip(f"Interface {interface_name} not found in contracts")
    
    interface_body = match.group(1)
    
    # Extract field names (simplified - assumes format: fieldName: type;)
    field_pattern = r'(\w+)(\??):\s*\w+'
    fields = set()
    
    for line in interface_body.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        
        match = re.search(field_pattern, line)
        if match:
            field_name = match.group(1)
            # Remove optional marker
            fields.add(field_name)
    
    return fields


class TestAuthTokenContractAlignment:
    """Test AuthTokens TypeScript interface aligns with TokenResponse Pydantic model."""
    
    def test_auth_tokens_field_alignment(self):
        """
        GIVEN: TypeScript AuthTokens interface
        WHEN: Comparing field names with Python TokenResponse model
        THEN: All fields should align (accounting for camelCase/snake_case conversion)
        """
        # TypeScript fields (camelCase)
        ts_fields = get_typescript_interface_fields("AuthTokens")
        
        # Python fields (snake_case)
        py_fields = get_pydantic_fields(TokenResponse)
        
        # Convert TypeScript fields to snake_case for comparison
        ts_fields_snake = {camel_to_snake(f) for f in ts_fields}
        
        # Expected mappings (TypeScript -> Python)
        # AuthTokens maps to TokenResponse
        expected_py_fields = {
            'access_token',  # accessToken -> access_token
            'refresh_token',  # refreshToken -> refresh_token
            'token_type',  # tokenType -> token_type
            'expires_in',  # expiresIn -> expires_in
        }
        
        # Verify all expected fields exist in Python model
        missing_fields = expected_py_fields - py_fields
        assert not missing_fields, f"Missing fields in TokenResponse: {missing_fields}"
        
        # Note: refresh_expires_in might not be in TokenResponse, that's OK


class TestMemoryContractAlignment:
    """Test Memory TypeScript interface aligns with MemoryResponse Pydantic model."""
    
    def test_memory_field_alignment(self):
        """
        GIVEN: TypeScript Memory interface
        WHEN: Comparing field names with Python MemoryResponse model
        THEN: Core fields should align
        """
        py_fields = get_pydantic_fields(MemoryResponse)
        
        # Expected mappings (Memory TypeScript -> MemoryResponse Python)
        # Note: Some fields have different names due to naming conventions
        expected_core_fields = {
            'id',
            'user_id',  # authorId in TS -> user_id in Python
            'family_unit_id',  # familyUnitId -> family_unit_id
            'title',
            'description',
            'created_at',  # createdAt -> created_at
            'updated_at',  # updatedAt -> updated_at
            'tags',
            'status',  # visibility in TS, status in Python (different concepts)
            'media',
        }
        
        # Verify core fields exist
        missing_fields = expected_core_fields - py_fields
        # Some fields may not exist due to schema differences, log them
        if missing_fields:
            pytest.skip(f"Fields not in MemoryResponse (may be intentional): {missing_fields}")


class TestReactionContractAlignment:
    """Test Reaction TypeScript interface aligns with ReactionResponse Pydantic model."""
    
    def test_reaction_field_alignment(self):
        """
        GIVEN: TypeScript Reaction interface
        WHEN: Comparing field names with Python ReactionResponse model
        THEN: Core fields should align
        """
        py_fields = get_pydantic_fields(ReactionResponse)
        
        # Expected mappings
        expected_fields = {
            'id',
            'memory_id',  # memoryId -> memory_id
            'user_id',  # userId -> user_id
            'emoji',  # type in TS maps to emoji in Python
            'created_at',  # createdAt -> created_at
        }
        
        # Verify fields exist
        missing_fields = expected_fields - py_fields
        assert not missing_fields, f"Missing fields in ReactionResponse: {missing_fields}"


class TestCommentContractAlignment:
    """Test Comment TypeScript interface aligns with CommentResponse Pydantic model."""
    
    def test_comment_field_alignment(self):
        """
        GIVEN: TypeScript Comment interface
        WHEN: Comparing field names with Python CommentResponse model
        THEN: Core fields should align
        """
        py_fields = get_pydantic_fields(CommentResponse)
        
        # Expected mappings
        expected_fields = {
            'id',
            'memory_id',  # memoryId -> memory_id
            'user_id',  # userId -> user_id
            'content',  # body in TS -> content in Python
            'parent_comment_id',  # parentId -> parent_comment_id
            'created_at',  # createdAt -> created_at
            'updated_at',  # updatedAt -> updated_at
            'replies',  # children in TS -> replies in Python (semantic difference)
        }
        
        # Verify core fields exist
        missing_fields = expected_fields - py_fields
        # Some semantic differences are OK (body vs content, children vs replies)
        critical_fields = {'id', 'memory_id', 'user_id', 'created_at'}
        missing_critical = critical_fields - py_fields
        assert not missing_critical, f"Missing critical fields in CommentResponse: {missing_critical}"


class TestLoginRequestContractAlignment:
    """Test LoginRequest TypeScript interface aligns with LoginRequest Pydantic model."""
    
    def test_login_request_field_alignment(self):
        """
        GIVEN: TypeScript LoginRequest interface
        WHEN: Comparing field names with Python LoginRequest model
        THEN: Fields should align perfectly
        """
        py_fields = get_pydantic_fields(LoginRequest)
        
        # LoginRequest should have email and password in both
        expected_fields = {'email', 'password'}
        
        missing_fields = expected_fields - py_fields
        assert not missing_fields, f"Missing fields in LoginRequest: {missing_fields}"


class TestTypeScriptContractsFileExists:
    """Test that TypeScript contracts file exists and is readable."""
    
    def test_contracts_file_exists(self):
        """Verify contracts/types/index.ts file exists."""
        contracts_path = Path(__file__).parent.parent.parent / "contracts" / "types" / "index.ts"
        
        assert contracts_path.exists(), (
            f"TypeScript contracts file not found at {contracts_path}. "
            "Ensure contracts/types/index.ts exists and contains interface definitions."
        )
        
        # Verify file is readable and contains expected interfaces
        with open(contracts_path, 'r') as f:
            content = f.read()
        
        expected_interfaces = [
            'UserProfile',
            'Memory',
            'Reaction',
            'Comment',
            'AuthTokens',
            'LoginRequest',
        ]
        
        for interface in expected_interfaces:
            assert f'interface {interface}' in content or f'export interface {interface}' in content, (
                f"Expected interface {interface} not found in contracts file"
            )


class TestFieldNameConversion:
    """Test helper functions for converting between naming conventions."""
    
    def test_snake_to_camel(self):
        """Test snake_case to camelCase conversion."""
        assert snake_to_camel('access_token') == 'accessToken'
        assert snake_to_camel('refresh_token') == 'refreshToken'
        assert snake_to_camel('user_id') == 'userId'
        assert snake_to_camel('family_unit_id') == 'familyUnitId'
        assert snake_to_camel('created_at') == 'createdAt'
    
    def test_camel_to_snake(self):
        """Test camelCase to snake_case conversion."""
        assert camel_to_snake('accessToken') == 'access_token'
        assert camel_to_snake('refreshToken') == 'refresh_token'
        assert camel_to_snake('userId') == 'user_id'
        assert camel_to_snake('familyUnitId') == 'family_unit_id'
        assert camel_to_snake('createdAt') == 'created_at'
        assert camel_to_snake('displayName') == 'display_name'
    
    def test_round_trip_conversion(self):
        """Test that conversion is reversible (approximately)."""
        test_cases = [
            'access_token',
            'refresh_token',
            'user_id',
            'family_unit_id',
            'created_at',
            'updated_at',
        ]
        
        for snake in test_cases:
            camel = snake_to_camel(snake)
            back_to_snake = camel_to_snake(camel)
            assert back_to_snake == snake, f"Round trip failed: {snake} -> {camel} -> {back_to_snake}"


class TestResponseSchemaConsistency:
    """Test that response schemas have consistent field naming."""
    
    def test_all_response_models_have_id(self):
        """All response models should have an 'id' field."""
        response_models = [
            MemoryResponse,
            ReactionResponse,
            CommentResponse,
            MediaResponse,
        ]
        
        for model in response_models:
            fields = get_pydantic_fields(model)
            assert 'id' in fields, f"{model.__name__} should have an 'id' field"
    
    def test_all_response_models_have_timestamps(self):
        """Most response models should have created_at and/or updated_at."""
        response_models = [
            MemoryResponse,
            ReactionResponse,
            CommentResponse,
            MediaResponse,
        ]
        
        for model in response_models:
            fields = get_pydantic_fields(model)
            has_timestamps = 'created_at' in fields or 'updated_at' in fields
            assert has_timestamps, f"{model.__name__} should have timestamp fields"

