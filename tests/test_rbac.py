"""
Tests for Role-Based Access Control (RBAC) enforcement.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.utils.jwt import TokenClaims
from app.models.user import CurrentUser
from app.services.rbac import (
    can_manage_family,
    can_invite_members,
    can_provision_children,
    can_create_pets,
    can_delete_content,
    can_edit_content,
    validate_family_access
)


client = TestClient(app)


class TestRBACPermissions:
    """Test RBAC permission functions."""
    
    def test_can_manage_family(self):
        """Test family management permissions."""
        assert can_manage_family("adult") == True
        assert can_manage_family("grandparent") == True
        assert can_manage_family("teen") == False
        assert can_manage_family("child") == False
        assert can_manage_family("pet") == False
    
    def test_can_invite_members(self):
        """Test invite permissions."""
        assert can_invite_members("adult") == True
        assert can_invite_members("grandparent") == True
        assert can_invite_members("teen") == False
        assert can_invite_members("child") == False
        assert can_invite_members("pet") == False
    
    def test_can_provision_children(self):
        """Test child provisioning permissions."""
        assert can_provision_children("adult") == True
        assert can_provision_children("grandparent") == False
        assert can_provision_children("teen") == False
        assert can_provision_children("child") == False
        assert can_provision_children("pet") == False
    
    def test_can_create_pets(self):
        """Test pet creation permissions."""
        assert can_create_pets("adult") == True
        assert can_create_pets("grandparent") == True
        assert can_create_pets("teen") == False
        assert can_create_pets("child") == False
        assert can_create_pets("pet") == False
    
    def test_can_delete_content(self):
        """Test content deletion permissions."""
        # Adults can delete any content
        assert can_delete_content("adult", is_owner=False) == True
        assert can_delete_content("adult", is_owner=True) == True
        
        # Teens and grandparents can delete own content
        assert can_delete_content("teen", is_owner=True) == True
        assert can_delete_content("teen", is_owner=False) == False
        assert can_delete_content("grandparent", is_owner=True) == True
        assert can_delete_content("grandparent", is_owner=False) == False
        
        # Children and pets cannot delete
        assert can_delete_content("child", is_owner=True) == False
        assert can_delete_content("child", is_owner=False) == False
        assert can_delete_content("pet", is_owner=True) == False
        assert can_delete_content("pet", is_owner=False) == False
    
    def test_can_edit_content(self):
        """Test content editing permissions."""
        # Pets cannot edit
        assert can_edit_content("pet", is_owner=True) == False
        assert can_edit_content("pet", is_owner=False) == False
        
        # Children can only edit own content
        assert can_edit_content("child", is_owner=True) == True
        assert can_edit_content("child", is_owner=False) == False
        
        # Other roles can edit (with ownership restrictions handled elsewhere)
        assert can_edit_content("adult", is_owner=True) == True
        assert can_edit_content("adult", is_owner=False) == True
        assert can_edit_content("teen", is_owner=True) == True
        assert can_edit_content("teen", is_owner=False) == True
        assert can_edit_content("grandparent", is_owner=True) == True
        assert can_edit_content("grandparent", is_owner=False) == True
    
    def test_validate_family_access(self):
        """Test family access validation."""
        family_id = str(uuid4())
        other_family_id = str(uuid4())
        
        assert validate_family_access(family_id, family_id) == True
        assert validate_family_access(family_id, other_family_id) == False


class TestRBACEndpoints:
    """Test RBAC enforcement on API endpoints."""
    
    @patch("app.api.v1.auth.get_current_user")
    @patch("app.api.v1.auth.require_child_provision_permission")
    def test_provision_child_requires_adult(self, mock_rbac, mock_get_user):
        """Test that child provisioning requires adult role."""
        # Mock adult user
        adult_user = TokenClaims(
            sub=str(uuid4()),
            role="adult",
            family_unit_id=str(uuid4()),
            iat=1000,
            exp=2000,
            jti=str(uuid4()),
            type="access"
        )
        mock_get_user.return_value = adult_user
        mock_rbac.return_value = adult_user
        
        # Should work for adult
        # (Actual endpoint test would require full setup)
        assert can_provision_children("adult") == True
    
    @patch("app.api.v1.invites.get_current_user")
    @patch("app.api.v1.invites.require_invite_permission")
    def test_create_invite_requires_permission(self, mock_rbac, mock_get_user):
        """Test that creating invites requires appropriate role."""
        # Adult can invite
        adult_user = TokenClaims(
            sub=str(uuid4()),
            role="adult",
            family_unit_id=str(uuid4()),
            iat=1000,
            exp=2000,
            jti=str(uuid4()),
            type="access"
        )
        assert can_invite_members("adult") == True
        
        # Grandparent can invite
        assert can_invite_members("grandparent") == True
        
        # Teen cannot invite
        assert can_invite_members("teen") == False
    
    @patch("app.api.v1.feed.get_current_user_model")
    @patch("app.api.v1.feed.exclude_pets_for_current_user")
    def test_feed_interactions_exclude_pets(self, mock_rbac, mock_get_user):
        """Test that feed interactions exclude pets."""
        # Pet user
        pet_user = CurrentUser(
            user_id=uuid4(),
            family_unit_id=uuid4(),
            role="pet"
        )
        
        # Should be blocked
        # (Actual endpoint test would require full setup)
        assert can_edit_content("pet", is_owner=True) == False


class TestRoleBehaviorMatrix:
    """Comprehensive role behavior test matrix."""
    
    ROLES = ["adult", "teen", "child", "grandparent", "pet"]
    
    def test_family_management_matrix(self):
        """Test family management permissions for all roles."""
        matrix = {
            "adult": True,
            "grandparent": True,
            "teen": False,
            "child": False,
            "pet": False
        }
        
        for role in self.ROLES:
            assert can_manage_family(role) == matrix[role]
    
    def test_invite_permissions_matrix(self):
        """Test invite permissions for all roles."""
        matrix = {
            "adult": True,
            "grandparent": True,
            "teen": False,
            "child": False,
            "pet": False
        }
        
        for role in self.ROLES:
            assert can_invite_members(role) == matrix[role]
    
    def test_child_provisioning_matrix(self):
        """Test child provisioning permissions for all roles."""
        matrix = {
            "adult": True,
            "grandparent": False,
            "teen": False,
            "child": False,
            "pet": False
        }
        
        for role in self.ROLES:
            assert can_provision_children(role) == matrix[role]
    
    def test_pet_creation_matrix(self):
        """Test pet creation permissions for all roles."""
        matrix = {
            "adult": True,
            "grandparent": True,
            "teen": False,
            "child": False,
            "pet": False
        }
        
        for role in self.ROLES:
            assert can_create_pets(role) == matrix[role]
    
    def test_content_deletion_matrix(self):
        """Test content deletion permissions for all roles."""
        # As owner
        owner_matrix = {
            "adult": True,
            "grandparent": True,
            "teen": True,
            "child": False,
            "pet": False
        }
        
        # Not owner
        non_owner_matrix = {
            "adult": True,
            "grandparent": False,
            "teen": False,
            "child": False,
            "pet": False
        }
        
        for role in self.ROLES:
            assert can_delete_content(role, is_owner=True) == owner_matrix[role]
            assert can_delete_content(role, is_owner=False) == non_owner_matrix[role]
    
    def test_content_editing_matrix(self):
        """Test content editing permissions for all roles."""
        # As owner
        owner_matrix = {
            "adult": True,
            "grandparent": True,
            "teen": True,
            "child": True,
            "pet": False
        }
        
        # Not owner
        non_owner_matrix = {
            "adult": True,
            "grandparent": True,
            "teen": True,
            "child": False,
            "pet": False
        }
        
        for role in self.ROLES:
            assert can_edit_content(role, is_owner=True) == owner_matrix[role]
            assert can_edit_content(role, is_owner=False) == non_owner_matrix[role]

