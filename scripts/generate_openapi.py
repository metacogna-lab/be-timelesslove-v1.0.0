#!/usr/bin/env python3
"""
Generate authoritative OpenAPI specification from FastAPI application.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def generate_openapi():
    """Generate OpenAPI spec and save to file."""
    openapi_schema = app.openapi()
    
    # Save as JSON
    output_path = Path(__file__).parent.parent / "docs" / "api" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"OpenAPI spec generated: {output_path}")
    print(f"Total paths: {len(openapi_schema.get('paths', {}))}")
    
    return openapi_schema


if __name__ == "__main__":
    generate_openapi()

