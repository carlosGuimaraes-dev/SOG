"""
Rate limiter compartilhado (slowapi, in-memory).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
