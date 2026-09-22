#!/usr/bin/env python3
"""
SatyaDhVani v2 — Voice Deepfake Detection Demo CLI
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from demo_dhwani import main

if __name__ == "__main__":
    sys.exit(main())
