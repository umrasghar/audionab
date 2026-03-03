"""AudioNab — backward-compatible entry point shim.

This file exists so `python audionab.py` still works.
The real code lives in the `audionab/` package.
"""
from audionab.__main__ import main

if __name__ == "__main__":
    main()
