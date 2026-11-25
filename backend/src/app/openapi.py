"""Exporta el contrato OpenAPI (Swagger): `python -m app.openapi <ruta.json>`."""

import json
import sys
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.main import build_state, create_app


def openapi_document() -> dict[str, Any]:
    return create_app(build_state(get_settings())).openapi()


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    target = Path(sys.argv[1])
    target.write_text(render(openapi_document()), encoding="utf-8")
    print(f"OpenAPI exportado a {target}")


if __name__ == "__main__":
    main()
