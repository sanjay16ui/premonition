#!/usr/bin/env python3
"""Start the PREMONITION FastAPI server."""

from __future__ import annotations

import uvicorn

from premonition.config.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "premonition.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
