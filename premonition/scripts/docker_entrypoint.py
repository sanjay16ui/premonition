#!/usr/bin/env python
"""Docker entrypoint — routes commands to PREMONITION scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COMMANDS = {
    "help": None,
    "train": ["python", "scripts/train.py", "--tier", "t1"],
    "train-t0": ["python", "scripts/train.py", "--tier", "t0"],
    "train-t2": ["python", "scripts/train.py", "--tier", "t2"],
    "explain": ["python", "scripts/explain.py", "--n-samples", "5"],
    "api": ["python", "scripts/run_api.py"],
    "test": ["python", "-m", "pytest", "tests/", "-v"],
}


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "help" or cmd not in COMMANDS:
        print("PREMONITION Docker Commands:")
        for name in COMMANDS:
            if name != "help":
                print(f"  docker compose run --rm premonition-ml {name}")
        sys.exit(0)

    result = subprocess.run(COMMANDS[cmd], cwd=Path(__file__).resolve().parents[1])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
