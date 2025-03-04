"""
Supabase client services for Noodle Projects.
Uses the official supabase-py client.
"""

from .client import get_supabase_client

__all__ = ["get_supabase_client"]