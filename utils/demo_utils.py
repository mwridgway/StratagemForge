"""
Demo file management utilities for StratagemForge
"""
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional

def ensure_demos_directory() -> str:
    """Ensure the demos directory exists and return its path"""
    demo_dir = "demos"
    if not os.path.exists(demo_dir):
        os.makedirs(demo_dir)
    return demo_dir

def get_demo_file_info(filename: str) -> Optional[Dict]:
    """Get detailed information about a demo file"""
    demo_dir = ensure_demos_directory()
    file_path = os.path.join(demo_dir, filename)
    
    if not os.path.exists(file_path) or not filename.endswith('.dem'):
        return None
    
    try:
        file_size = os.path.getsize(file_path)
        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        file_created = datetime.fromtimestamp(os.path.getctime(file_path))
        
        return {
            'filename': filename,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'modified': file_modified,
            'created': file_created,
            'modified_str': file_modified.strftime('%Y-%m-%d %H:%M'),
            'created_str': file_created.strftime('%Y-%m-%d %H:%M'),
            'path': file_path,
            'status': 'Available'
        }
    except Exception as e:
        print(f"Error getting info for {filename}: {e}")
        return None

def list_demo_files() -> List[Dict]:
    """Get a list of all demo files with their information"""
    demo_dir = ensure_demos_directory()
    demo_files = []
    
    try:
        for filename in os.listdir(demo_dir):
            if filename.endswith('.dem'):
                info = get_demo_file_info(filename)
                if info:
                    demo_files.append(info)
    except Exception as e:
        print(f"Error listing demo files: {e}")
    
    # Sort by modification date (newest first)
    demo_files.sort(key=lambda x: x['modified'], reverse=True)
    return demo_files

def validate_demo_file(filename: str, content: bytes) -> Dict[str, str]:
    """Validate if the uploaded file is a valid demo file"""
    result = {'valid': False, 'message': ''}
    
    # Check file extension
    if not filename.endswith('.dem'):
        result['message'] = 'Invalid file extension. Only .dem files are allowed.'
        return result
    
    # Check file size (demos are typically between 10KB and 200MB)
    size_mb = len(content) / (1024 * 1024)
    if size_mb < 0.01:  # Less than 10KB
        result['message'] = 'File too small to be a valid demo file.'
        return result
    elif size_mb > 500:  # More than 500MB
        result['message'] = 'File too large. Demo files are typically under 500MB.'
        return result
    
    # Basic header validation (CS2 demos start with specific bytes)
    if len(content) > 8:
        # Check for common demo file signatures
        header = content[:8]
        # This is a simplified check - real validation would be more comprehensive
        if b'HL2DEMO' in content[:100] or b'PBDEMS2' in content[:100]:
            result['valid'] = True
            result['message'] = 'Valid demo file detected.'
        else:
            result['message'] = 'File does not appear to be a valid CS2 demo file.'
    else:
        result['message'] = 'File too small to validate.'
    
    return result

def delete_demo_file(filename: str) -> bool:
    """Delete a demo file"""
    demo_dir = ensure_demos_directory()
    file_path = os.path.join(demo_dir, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting {filename}: {e}")
    
    return False

def get_storage_info() -> Dict:
    """Get information about demo storage usage"""
    demo_dir = ensure_demos_directory()
    total_size = 0
    file_count = 0
    
    try:
        for filename in os.listdir(demo_dir):
            if filename.endswith('.dem'):
                file_path = os.path.join(demo_dir, filename)
                total_size += os.path.getsize(file_path)
                file_count += 1
    except Exception as e:
        print(f"Error getting storage info: {e}")
    
    return {
        'total_files': file_count,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
    }
