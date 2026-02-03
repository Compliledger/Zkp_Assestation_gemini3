"""
Storage layer for ZKP Attestation Agent
Supports in-memory storage for demo mode
"""

from .memory_store import memory_store

__all__ = ["memory_store"]
