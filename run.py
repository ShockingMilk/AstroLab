#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

sys.path.insert(
    index=0,
    object=str(SRC)
)

from astrocam.app.main import main

if __name__ == "__main__":
    main()