#!/usr/bin/env python3
"""
Setup script for AI Facebook Content Generator
"""

import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="fb_posts",
    version="0.1.0",
    description="Multi-File Upload System Enhancement - Phase 5.5",
    author="Trevor Chimtengo",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "python-telegram-bot>=20.0",
        "asyncio>=3.4.3",
        "psutil>=5.9.0",
        "prometheus-client>=0.14.0",
        "statsd>=3.3.0",
        "python-dotenv>=0.19.0",
        "pydantic>=1.9.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0"
        ]
    }
) 