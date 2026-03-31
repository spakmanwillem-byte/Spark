"""
File Manager Routes - Admin only
Browse, read, and edit Spark codebase files
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter()

# Allowed directories
ALLOWED_DIRS = [
    "/app/backend",
    "/app/frontend/src"
]

# File extensions we support
SUPPORTED_EXTENSIONS = [
    '.py', '.js', '.jsx', '.json', '.css', '.html', '.md', 
    '.txt', '.yaml', '.yml', '.env.example'
]

# Protected files (read-only even for gradatie 1)
PROTECTED_FILES = [
    '/app/backend/.env',
    '/app/backend/server.py'
]


class SaveFileRequest(BaseModel):
    path: str
    content: str
    user_id: str
    user_gradatie: int


def is_path_allowed(file_path: str) -> bool:
    """Check if path is in allowed directories"""
    abs_path = os.path.abspath(file_path)
    return any(abs_path.startswith(allowed) for allowed in ALLOWED_DIRS)


def is_file_supported(file_path: str) -> bool:
    """Check if file extension is supported"""
    return any(file_path.endswith(ext) for ext in SUPPORTED_EXTENSIONS)


def get_file_type(file_path: str) -> str:
    """Get file type based on extension"""
    ext = Path(file_path).suffix
    type_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.json': 'json',
        '.css': 'css',
        '.html': 'html',
        '.md': 'markdown',
        '.txt': 'text',
        '.yaml': 'yaml',
        '.yml': 'yaml'
    }
    return type_map.get(ext, 'text')


@router.get("/tree")
async def get_file_tree(user_gradatie: int = Query(...)):
    """
    Get file tree of allowed directories
    Gradatie 1, 2, 3 can view
    """
    if user_gradatie > 3:
        raise HTTPException(status_code=403, detail="Access denied")
    
    tree = []
    
    for base_dir in ALLOWED_DIRS:
        if not os.path.exists(base_dir):
            continue
            
        dir_name = os.path.basename(base_dir)
        dir_tree = {
            'name': dir_name,
            'path': base_dir,
            'type': 'directory',
            'children': []
        }
        
        # Walk directory tree
        for root, dirs, files in os.walk(base_dir):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'build', 'dist']]
            
            for file in sorted(files):
                file_path = os.path.join(root, file)
                
                # Only include supported files
                if not is_file_supported(file_path):
                    continue
                
                # Skip hidden files
                if file.startswith('.') and file != '.env.example':
                    continue
                
                file_info = {
                    'name': file,
                    'path': file_path,
                    'type': 'file',
                    'file_type': get_file_type(file_path),
                    'size': os.path.getsize(file_path),
                    'editable': user_gradatie == 1 and file_path not in PROTECTED_FILES
                }
                
                dir_tree['children'].append(file_info)
        
        tree.append(dir_tree)
    
    return {
        'success': True,
        'tree': tree,
        'total_files': sum(len(d['children']) for d in tree)
    }


@router.get("/content")
async def get_file_content(
    file_path: str = Query(...),
    user_gradatie: int = Query(...)
):
    """
    Get file content
    Gradatie 1, 2, 3 can read
    """
    if user_gradatie > 3:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Security checks
    if not is_path_allowed(file_path):
        raise HTTPException(status_code=403, detail="Path not allowed")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="Not a file")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'success': True,
            'path': file_path,
            'content': content,
            'file_type': get_file_type(file_path),
            'size': len(content),
            'lines': content.count('\n') + 1,
            'editable': user_gradatie == 1 and file_path not in PROTECTED_FILES,
            'protected': file_path in PROTECTED_FILES
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


def validate_syntax(file_path: str, content: str) -> Dict:
    """Validate syntax for Python and JavaScript files"""
    validation = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    file_type = get_file_type(file_path)
    
    # Python validation
    if file_type == 'python':
        try:
            import ast
            ast.parse(content)
        except SyntaxError as e:
            validation['valid'] = False
            validation['errors'].append({
                'line': e.lineno,
                'message': f'SyntaxError: {e.msg}',
                'text': e.text.strip() if e.text else ''
            })
        except Exception as e:
            validation['warnings'].append(f'Could not fully validate: {str(e)}')
    
    # JavaScript validation (basic check for common issues)
    elif file_type == 'javascript':
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            validation['warnings'].append(f'Unmatched braces: {open_braces} opening, {close_braces} closing')
        
        # Check for unmatched parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            validation['warnings'].append(f'Unmatched parentheses: {open_parens} opening, {close_parens} closing')
    
    # JSON validation
    elif file_type == 'json':
        try:
            import json
            json.loads(content)
        except json.JSONDecodeError as e:
            validation['valid'] = False
            validation['errors'].append({
                'line': e.lineno,
                'message': f'JSON Error: {e.msg}',
                'text': ''
            })
    
    return validation


@router.post("/validate")
async def validate_file(req: SaveFileRequest):
    """
    Validate file syntax without saving
    Gradatie 1, 2, 3 can validate
    """
    if req.user_gradatie > 3:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not is_path_allowed(req.path):
        raise HTTPException(status_code=403, detail="Path not allowed")
    
    validation = validate_syntax(req.path, req.content)
    
    return {
        'success': True,
        'validation': validation
    }


@router.post("/save")
async def save_file(req: SaveFileRequest):
    """
    Save file content with syntax validation
    ONLY Gradatie 1 can edit
    """
    if req.user_gradatie != 1:
        raise HTTPException(status_code=403, detail="Only admin (gradatie 1) can edit files")
    
    # Security checks
    if not is_path_allowed(req.path):
        raise HTTPException(status_code=403, detail="Path not allowed")
    
    if req.path in PROTECTED_FILES:
        raise HTTPException(status_code=403, detail="This file is protected and cannot be edited")
    
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Validate syntax before saving
    validation = validate_syntax(req.path, req.content)
    if not validation['valid']:
        return {
            'success': False,
            'validation': validation,
            'message': 'Syntax errors detected. Fix errors before saving.'
        }
    
    # Create backup before saving
    backup_path = None
    try:
        backup_path = req.path + '.backup'
        if os.path.exists(req.path):
            with open(req.path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    
    # Save new content
    try:
        with open(req.path, 'w', encoding='utf-8') as f:
            f.write(req.content)
        
        return {
            'success': True,
            'message': 'File saved successfully',
            'path': req.path,
            'backup_created': os.path.exists(backup_path) if backup_path else False,
            'validation': validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.get("/list")
async def list_files(
    directory: str = Query(...),
    user_gradatie: int = Query(...)
):
    """
    List files in a directory
    """
    if user_gradatie > 3:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not is_path_allowed(directory):
        raise HTTPException(status_code=403, detail="Path not allowed")
    
    if not os.path.exists(directory):
        raise HTTPException(status_code=404, detail="Directory not found")
    
    try:
        items = []
        for item in sorted(os.listdir(directory)):
            item_path = os.path.join(directory, item)
            
            # Skip hidden and unwanted
            if item.startswith('.') or item in ['__pycache__', 'node_modules']:
                continue
            
            if os.path.isfile(item_path):
                if not is_file_supported(item_path):
                    continue
                
                items.append({
                    'name': item,
                    'path': item_path,
                    'type': 'file',
                    'file_type': get_file_type(item_path),
                    'size': os.path.getsize(item_path)
                })
            elif os.path.isdir(item_path):
                items.append({
                    'name': item,
                    'path': item_path,
                    'type': 'directory'
                })
        
        return {
            'success': True,
            'directory': directory,
            'items': items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing directory: {str(e)}")
