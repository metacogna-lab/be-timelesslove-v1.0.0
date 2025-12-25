# Timeless Love Backend

Backend API for the Timeless Love family social platform.

## Features

- Custom JWT authentication with role-based access control
- User registration for multiple roles (Adult, Teen, Child, Grandparent, Pet)
- Family unit management
- Invitation system with expiring tokens
- Secure token refresh with rotation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Configure `.env` with your Supabase credentials and JWT secret.

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API route handlers
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic
│   ├── utils/           # Utilities (JWT, security)
│   └── db/              # Database clients
├── docs/                # Documentation
├── tests/               # Test files
└── requirements.txt     # Python dependencies
```

## Development

See `AGENTS.md` for backend agent behavior guidelines.

