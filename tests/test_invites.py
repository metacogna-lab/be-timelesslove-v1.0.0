"""
Unit and integration tests for invitation endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status
from datetime import datetime, timedelta
from uuid import uuid4


class TestInvitationService:
    """Test invitation service functions."""
    
    @pytest.mark.asyncio
    @patch('app.services.invite_service.get_supabase_service_client')
    async def test_create_invitation(
        self,
        mock_supabase_client,
        sample_family_unit_id,
        sample_user_id
    ):
        """Test invitation creation."""
        from app.services.invite_service import create_invitation
        
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value.data = [{
            "id": str(uuid4()),
            "family_unit_id": sample_family_unit_id,
            "invited_by": sample_user_id,
            "email": "invitee@example.com",
            "role": "teen",
            "token": "test_token",
            "status": "pending",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }]
        mock_client.table.return_value = mock_table
        mock_supabase_client.return_value = mock_client
        
        # Create invitation
        invite = await create_invitation(
            family_unit_id=sample_family_unit_id,
            invited_by=sample_user_id,
            email="invitee@example.com",
            role="teen"
        )
        
        # Assertions
        assert invite.email == "invitee@example.com"
        assert invite.role == "teen"
        assert invite.status == "pending"
        assert invite.token is not None
    
    @pytest.mark.asyncio
    @patch('app.services.invite_service.get_supabase_service_client')
    async def test_validate_invitation_valid(
        self,
        mock_supabase_client
    ):
        """Test validation of valid invitation."""
        from app.services.invite_service import validate_invitation
        
        # Setup mock
        future_date = datetime.utcnow() + timedelta(days=7)
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value.data = [{
            "id": str(uuid4()),
            "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
            "invited_by": "550e8400-e29b-41d4-a716-446655440000",
            "email": "invitee@example.com",
            "role": "teen",
            "token": "valid_token",
            "status": "pending",
            "expires_at": future_date.isoformat(),
            "accepted_at": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }]
        mock_client.table.return_value = mock_table
        mock_supabase_client.return_value = mock_client
        
        # Validate invitation
        is_valid, invite, error = await validate_invitation("valid_token")
        
        # Assertions
        assert is_valid is True
        assert invite is not None
        assert error is None
    
    @pytest.mark.asyncio
    @patch('app.services.invite_service.get_supabase_service_client')
    async def test_validate_invitation_expired(
        self,
        mock_supabase_client
    ):
        """Test validation of expired invitation."""
        from app.services.invite_service import validate_invitation
        
        # Setup mock
        past_date = datetime.utcnow() - timedelta(days=1)
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value.data = [{
            "id": str(uuid4()),
            "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
            "invited_by": "550e8400-e29b-41d4-a716-446655440000",
            "email": "invitee@example.com",
            "role": "teen",
            "token": "expired_token",
            "status": "pending",
            "expires_at": past_date.isoformat(),
            "accepted_at": None,
            "created_at": (datetime.utcnow() - timedelta(days=8)).isoformat(),
            "updated_at": (datetime.utcnow() - timedelta(days=8)).isoformat()
        }]
        mock_client.table.return_value = mock_table
        mock_supabase_client.return_value = mock_client
        
        # Validate invitation
        is_valid, invite, error = await validate_invitation("expired_token")
        
        # Assertions
        assert is_valid is False
        assert error is not None
        assert "invitation not found" in error.lower()


class TestInvitationEndpoints:
    """Test invitation API endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.api.v1.invites.create_invitation')
    @patch('app.api.v1.invites.check_user_exists')
    async def test_create_invite_success(
        self,
        mock_check_exists,
        mock_create_invite,
        client,
        sample_access_token
    ):
        """Test successful invitation creation."""
        from app.models.invite import Invite
        from datetime import datetime, timedelta
        
        # Setup mocks
        mock_check_exists.return_value = False
        mock_create_invite.return_value = Invite(
            id=uuid4(),
            family_unit_id=uuid4(),
            invited_by=uuid4(),
            email="invitee@example.com",
            role="teen",
            token="test_token",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Make request
        response = client.post(
            "/api/v1/invites",
            headers={"Authorization": f"Bearer {sample_access_token}"},
            json={
                "email": "invitee@example.com",
                "role": "teen"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["email"] == "invitee@example.com"
        assert data["role"] == "teen"
        assert "invite_link" in data
    
    def test_create_invite_unauthorized(self, client):
        """Test invitation creation without authentication."""
        response = client.post(
            "/api/v1/invites",
            json={
                "email": "invitee@example.com",
                "role": "teen"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    @patch('app.api.v1.invites.validate_invitation')
    async def test_validate_invite_endpoint(
        self,
        mock_validate,
        client
    ):
        """Test invitation validation endpoint."""
        from app.models.invite import Invite
        from datetime import datetime, timedelta
        
        # Setup mock
        mock_validate.return_value = (
            True,
            Invite(
                id=uuid4(),
                family_unit_id=uuid4(),
                invited_by=uuid4(),
                email="invitee@example.com",
                role="teen",
                token="test_token",
                status="pending",
                expires_at=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            None
        )
        
        # Make request
        response = client.get("/api/v1/invites/test_token")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert "invite" in data
    
    @pytest.mark.asyncio
    @patch('app.api.v1.invites.validate_invitation')
    @patch('app.api.v1.invites.register_user')
    @patch('app.services.invite_service.accept_invitation')
    async def test_accept_invite_success(
        self,
        mock_accept,
        mock_register,
        mock_validate,
        client
    ):
        """Test successful invitation acceptance."""
        from app.models.invite import Invite
        from datetime import datetime, timedelta
        from app.schemas.auth import RegisterResponse, TokenResponse
        
        # Setup mocks
        invite = Invite(
            id=uuid4(),
            family_unit_id=uuid4(),
            invited_by=uuid4(),
            email="invitee@example.com",
            role="teen",
            token="test_token",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_validate.return_value = (True, invite, None)
        mock_register.return_value = RegisterResponse(
            user_id=str(uuid4()),
            email="invitee@example.com",
            role="teen",
            family_unit_id=str(invite.family_unit_id),
            tokens=TokenResponse(
                access_token="token",
                refresh_token="refresh",
                expires_in=900
            )
        )
        mock_accept.return_value = None
        
        # Make request
        response = client.post(
            "/api/v1/invites/test_token/accept",
            json={
                "email": "invitee@example.com",
                "password": "SecurePass123!",
                "display_name": "Invited User"
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "accepted"

