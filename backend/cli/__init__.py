"""
CLI tools for the CRM project.

Provides command-line utilities for code generation, database management,
and development workflows.
"""

from cli.crud_generate import app as crud_app

__all__ = ["crud_app"]
