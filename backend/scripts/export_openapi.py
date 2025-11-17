#!/usr/bin/env python3
"""
Export OpenAPI specification from FastAPI app to JSON file.

This script generates the OpenAPI schema from the FastAPI application
and saves it to openapi.json for frontend TypeScript client generation.

Usage:
    poetry run python scripts/export_openapi.py
"""

import json
from pathlib import Path

# Import the FastAPI app
from app.main import app


def export_openapi_spec() -> None:
    """Export OpenAPI spec to backend/openapi.json."""

    # Get the OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Determine output path (backend root directory)
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    output_path = backend_dir / "openapi.json"

    # Write schema to file with pretty formatting
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI specification exported to: {output_path}")
    print(f"📊 Paths: {len(openapi_schema.get('paths', {}))}")
    print(f"📦 Schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))}")


if __name__ == "__main__":
    export_openapi_spec()
