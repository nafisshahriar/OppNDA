"""
Path utilities for cross-platform path handling and validation.

Provides functions for:
- Resolving absolute paths from relative or user-specified paths
- Validating path existence and permissions
- Path normalization across Windows, Linux, macOS
- Safe path construction
"""

import os
import pathlib
from typing import Optional, Tuple


def resolve_absolute_path(path: str) -> str:
    """
    Resolve a path to its absolute form.
    
    Handles:
    - Relative paths (converted to absolute based on current working directory)
    - Tilde expansion (~/)
    - Path separator normalization
    
    Args:
        path: Path string (can be relative or absolute)
    
    Returns:
        Absolute path as string
    
    Raises:
        ValueError: If path is empty or contains invalid characters
    """
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string")
    
    # Expand user home (~)
    expanded = os.path.expanduser(path.strip())
    
    # Convert to absolute path
    absolute = os.path.abspath(expanded)
    
    return absolute


def validate_path(path: str, must_exist: bool = False, 
                  must_be_dir: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate if a path is accessible and meets requirements.
    
    Args:
        path: Path to validate
        must_exist: If True, path must exist
        must_be_dir: If True, path must be a directory
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    try:
        absolute_path = resolve_absolute_path(path)
        
        if must_exist and not os.path.exists(absolute_path):
            return False, f"Path does not exist: {absolute_path}"
        
        if must_be_dir:
            if not os.path.isdir(absolute_path):
                return False, f"Path is not a directory: {absolute_path}"
            # Check if readable
            if not os.access(absolute_path, os.R_OK):
                return False, f"No read permission: {absolute_path}"
        
        # Check general accessibility
        if os.path.exists(absolute_path):
            if not os.access(absolute_path, os.R_OK):
                return False, f"Path is not readable: {absolute_path}"
        
        return True, None
    
    except Exception as e:
        return False, str(e)


def safe_path_join(*parts: str) -> str:
    """
    Safely join path components and return absolute path.
    
    Args:
        *parts: Path components to join
    
    Returns:
        Absolute joined path
    """
    if not parts:
        raise ValueError("At least one path component required")
    
    joined = os.path.join(*parts)
    return resolve_absolute_path(joined)


def normalize_path_separators(path: str) -> str:
    """
    Normalize path separators to forward slashes for consistency.
    Useful for storing paths in configs.
    
    Args:
        path: Path string
    
    Returns:
        Path with normalized separators
    """
    return path.replace('\\', '/')


def get_relative_path(full_path: str, base_path: str) -> str:
    """
    Get relative path from base_path to full_path.
    
    Args:
        full_path: The target path
        base_path: The base path to be relative to
    
    Returns:
        Relative path string
    """
    try:
        full_abs = resolve_absolute_path(full_path)
        base_abs = resolve_absolute_path(base_path)
        return os.path.relpath(full_abs, base_abs)
    except ValueError:
        return full_path


def is_path_within(target_path: str, base_path: str) -> bool:
    """
    Check if target_path is within base_path (for security validation).
    
    Args:
        target_path: Path to check
        base_path: Base/parent path
    
    Returns:
        True if target is within base
    """
    try:
        target_abs = resolve_absolute_path(target_path)
        base_abs = resolve_absolute_path(base_path)
        
        # Resolve any symlinks for comparison
        target_real = os.path.realpath(target_abs)
        base_real = os.path.realpath(base_abs)
        
        return target_real.startswith(base_real)
    except:
        return False
