---
title: Contributing
description: Development workflow, code structure, and testing guidelines
sidebar:
  order: 9
---

# Contributing

This guide covers the development workflow, code structure, testing guidelines, and best practices for contributing to the Timeless Love backend.

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd timelesslove-alpha/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow code style guidelines (see below)
- Write tests for new features
- Update documentation as needed

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_memories.py

# Run with coverage
pytest --cov=app tests/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Structure

### Project Layout

```
backend/
├── app/
│   ├── api/v1/          # API route handlers
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── memories.py  # Memory endpoints
│   │   ├── feed.py      # Feed endpoints
│   │   ├── storage.py   # Storage endpoints
│   │   └── invites.py   # Invitation endpoints
│   ├── models/          # Database models (Pydantic)
│   ├── schemas/         # Request/response schemas
│   ├── services/        # Business logic
│   ├── utils/           # Utilities (JWT, security)
│   ├── db/              # Database clients
│   ├── dependencies/    # FastAPI dependencies
│   └── main.py          # Application entry point
├── docs/                # Documentation
├── tests/               # Test files
├── db/migrations/       # Database migrations
└── requirements.txt    # Python dependencies
```

### Code Organization Principles

1. **Separation of Concerns**
   - API layer: HTTP handling only
   - Service layer: Business logic
   - Data layer: Database operations

2. **Dependency Injection**
   - Use FastAPI dependencies for authentication
   - Inject services rather than instantiating directly

3. **Error Handling**
   - Use HTTPException for API errors
   - Log errors with context
   - Return consistent error formats

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these additions:

- **Line Length**: 100 characters (soft limit)
- **Imports**: Group by standard library, third-party, local
- **Docstrings**: Use Google-style docstrings

### Example

```python
"""
Service for memory operations.

This module provides functions for creating, reading, updating,
and deleting memories with associated media.
"""

from typing import Optional, List
from uuid import UUID
from app.models.memory import Memory
from app.services.memory_service import create_memory


async def create_memory_endpoint(
    user_id: UUID,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> Memory:
    """
    Create a new memory.
    
    Args:
        user_id: User UUID creating the memory
        title: Optional memory title
        description: Optional memory description
    
    Returns:
        Created Memory object
    
    Raises:
        HTTPException: If creation fails
    """
    ...
```

### Type Hints

Always use type hints:

```python
from typing import Optional, List
from uuid import UUID

async def get_memory(memory_id: UUID) -> Optional[Memory]:
    ...
```

### Naming Conventions

- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_`

## Testing Guidelines

### Test Structure

Tests mirror the application structure:

```
tests/
├── conftest.py          # Pytest fixtures
├── test_auth.py        # Authentication tests
├── test_memories.py    # Memory tests
├── test_feed.py        # Feed tests
├── test_rbac.py        # RBAC tests
└── test_storage.py     # Storage tests
```

### Writing Tests

```python
import pytest
from uuid import uuid4
from app.services.memory_service import create_memory

@pytest.mark.asyncio
async def test_create_memory():
    """Test memory creation."""
    user_id = uuid4()
    family_unit_id = uuid4()
    
    memory = await create_memory(
        user_id=user_id,
        family_unit_id=family_unit_id,
        title="Test Memory"
    )
    
    assert memory.id is not None
    assert memory.title == "Test Memory"
    assert memory.user_id == user_id
```

### Test Fixtures

Use fixtures for common setup:

```python
# conftest.py
import pytest
from app.db.supabase import get_supabase_service_client

@pytest.fixture
async def test_user():
    """Create a test user."""
    ...
    return user

@pytest.fixture
async def test_family():
    """Create a test family unit."""
    ...
    return family
```

### Test Categories

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test API endpoints
3. **Contract Tests**: Verify API contracts
4. **RBAC Tests**: Test permission enforcement

### Running Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_memories.py::test_create_memory

# With coverage
pytest --cov=app --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## API Development

### Adding New Endpoints

1. **Define Schema** (`app/schemas/`)
```python
from pydantic import BaseModel

class CreateFeatureRequest(BaseModel):
    name: str
    description: Optional[str] = None
```

2. **Create Service** (`app/services/`)
```python
async def create_feature(name: str, description: Optional[str]) -> Feature:
    ...
```

3. **Add Endpoint** (`app/api/v1/`)
```python
@router.post("/features", response_model=FeatureResponse)
async def create_feature(
    request: CreateFeatureRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    ...
```

4. **Write Tests** (`tests/`)
```python
async def test_create_feature():
    ...
```

5. **Update Documentation** (`docs/api/`)

### API Versioning

- All endpoints under `/api/v1/`
- Breaking changes require version increment
- Document changes in API documentation

## Database Migrations

### Creating Migrations

1. Create migration file in `db/migrations/`:
```sql
-- Migration: 005_add_feature_table.sql
-- Purpose: Add feature table

CREATE TABLE IF NOT EXISTS features (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

2. Apply migration via Supabase Dashboard or migration script

### Migration Guidelines

- Number migrations sequentially
- Include purpose comment
- Test migrations on development database first
- Never modify existing migrations (create new ones)

## Documentation

### Code Documentation

- **Docstrings**: All public functions/classes
- **Type Hints**: Always include type hints
- **Comments**: Explain why, not what

### API Documentation

- Update OpenAPI spec (`docs/api/openapi.yaml`)
- Update API reference docs (`docs/api/`)
- Include request/response examples

### Developer Documentation

- Update feature guides (`docs/features/`)
- Update architecture docs (`docs/architecture/`)
- Keep examples up to date

## Best Practices

### Security

1. **Always Validate Input**: Use Pydantic schemas
2. **Enforce RBAC**: Use RBAC dependencies
3. **Validate Family Access**: Check family_unit_id
4. **Never Log Sensitive Data**: No passwords, tokens, PII

### Performance

1. **Use Background Tasks**: For non-blocking operations
2. **Optimize Queries**: Use indexes, limit results
3. **Cache When Appropriate**: Cache access URLs, feed scores
4. **Batch Operations**: When possible

### Error Handling

1. **Use HTTPException**: For API errors
2. **Log Errors**: With context (user_id, request_id)
3. **Return Consistent Format**: Standard error responses
4. **Handle Edge Cases**: Validate all inputs

### Code Quality

1. **Keep Functions Small**: Single responsibility
2. **Avoid Duplication**: Extract common logic
3. **Use Type Hints**: Always
4. **Write Tests**: For new features

## Related Documentation

- [Getting Started](../getting-started.md)
- [Architecture Overview](../architecture/overview.md)
- [Agent Guidelines](../../AGENTS.md)

