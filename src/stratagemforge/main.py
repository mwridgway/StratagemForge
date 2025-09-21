from __future__ import annotations

import uvicorn

from .core.app import create_app
from .core.config import get_settings


app = create_app()


def run() -> None:  # pragma: no cover - convenience wrapper
    settings = get_settings()
    uvicorn.run(
        "stratagemforge.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":  # pragma: no cover
    run()
