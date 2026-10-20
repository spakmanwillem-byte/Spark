"""
Files & Module Sandbox Routes
Intern zoeksysteem voor bestanden + sandbox voor nieuwe modules
"""
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os
from urllib.parse import quote
import json
import subprocess
import shutil
from datetime import datetime, timezone

router = APIRouter(tags=["files"])

ALLOWED_DIRS = ["/app/backend", "/app/frontend/src", "/app/memory"]
# v14_files_alle_types_001 (Willem 20-10: "alle bestandstypen die ik gebruik in Spark moet ik kunnen kiezen")
TEXT_EXT = ['.py', '.js', '.jsx', '.json', '.jsonl', '.css', '.html', '.md', '.txt', '.yaml', '.yml', '.csv', '.log', '.sh', '.toml', '.ini', '.xml', '.svg']
BINARY_EXT = ['.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.webp', '.gif', '.webm', '.wav', '.mp3', '.ogg', '.mp4', '.zip']
SUPPORTED_EXT = TEXT_EXT + BINARY_EXT
MIME = {'.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webm': 'video/webm',
        '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.mp4': 'video/mp4', '.zip': 'application/zip'}
PROTECTED_FILES = [
    '/app/backend/.env',
    '/app/backend/server.py',
    '/app/memory/test_credentials.md',  # bevat admin sleutelwoord — niet via UI bewerken
]
SANDBOX_DIR = "/app/backend/sandbox/modules"


def _is_allowed(path: str) -> bool:
    return any(os.path.abspath(path).startswith(d) for d in ALLOWED_DIRS)

def _is_supported(path: str) -> bool:
    return any(path.lower().endswith(e) for e in SUPPORTED_EXT)


def _is_binary(path: str) -> bool:
    return any(path.lower().endswith(e) for e in BINARY_EXT)

def _file_type(path: str) -> str:
    m = {'.py':'python','.js':'javascript','.jsx':'javascript','.json':'json','.jsonl':'jsonl','.css':'css','.html':'html','.md':'markdown','.txt':'text','.yaml':'yaml','.yml':'yaml',
         '.csv':'csv','.log':'log','.pdf':'pdf','.docx':'word','.xlsx':'excel','.jpg':'image','.jpeg':'image','.png':'image','.webp':'image','.gif':'image','.svg':'svg',
         '.webm':'video','.mp4':'video','.wav':'audio','.mp3':'audio','.ogg':'audio','.zip':'zip'}
    return m.get(Path(path).suffix.lower(), 'text')


# ============ FILE BROWSER ============

@router.get("/files/tree")
async def get_file_tree():
    """Get complete file tree of allowed directories"""
    tree = []
    for base_dir in ALLOWED_DIRS:
        if not os.path.exists(base_dir):
            continue
        files = []
        for root, dirs, filenames in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git', 'build', 'dist', 'sandbox']]
            for f in sorted(filenames):
                fp = os.path.join(root, f)
                if not _is_supported(fp) or f.startswith('.'):
                    continue
                files.append({
                    "name": f,
                    "path": fp,
                    "directory": os.path.relpath(os.path.dirname(fp), base_dir),
                    "file_type": _file_type(fp),
                    "size": os.path.getsize(fp),
                    "protected": fp in PROTECTED_FILES,
                })
        tree.append({"name": os.path.basename(base_dir), "base": base_dir, "files": files})
    total = sum(len(d["files"]) for d in tree)
    return {"success": True, "tree": tree, "total_files": total}


@router.get("/files/content")
async def get_file_content(file_path: str = Query(...)):
    """Read file content"""
    if not _is_allowed(file_path):
        raise HTTPException(status_code=403, detail="Pad niet toegestaan")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")
    if _is_binary(file_path):
        return {"success": True, "path": file_path, "content": "", "binary": True, "file_type": _file_type(file_path),
                "size": os.path.getsize(file_path), "raw_url": f"/api/files/raw?file_path={quote(file_path)}", "protected": True}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return {
            "success": True, "path": file_path, "content": content,
            "file_type": _file_type(file_path), "lines": content.count('\n') + 1,
            "protected": file_path in PROTECTED_FILES,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/raw")
async def get_file_raw(file_path: str = Query(...)):
    """Binaire bestanden (pdf, afbeelding, audio, video) inline tonen/downloaden — alleen binnen ALLOWED_DIRS."""
    if not _is_allowed(file_path) or not _is_supported(file_path):
        raise HTTPException(status_code=403, detail="Pad niet toegestaan")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")
    return FileResponse(file_path, media_type=MIME.get(Path(file_path).suffix.lower(), "application/octet-stream"), filename=os.path.basename(file_path))


class SaveRequest(BaseModel):
    path: str
    content: str

@router.post("/files/save")
async def save_file(req: SaveRequest):
    """Save file with syntax validation"""
    if not _is_allowed(req.path):
        raise HTTPException(status_code=403, detail="Pad niet toegestaan")
    if req.path in PROTECTED_FILES:
        raise HTTPException(status_code=403, detail="Dit bestand is beschermd")
    if not os.path.isfile(req.path):
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    validation = _validate_syntax(req.path, req.content)
    if not validation["valid"]:
        return {"success": False, "validation": validation}

    # Backup
    try:
        with open(req.path, 'r', encoding='utf-8') as f:
            backup = f.read()
        with open(req.path + '.bak', 'w', encoding='utf-8') as f:
            f.write(backup)
    except Exception:
        pass

    with open(req.path, 'w', encoding='utf-8') as f:
        f.write(req.content)
    return {"success": True, "validation": validation}


def _validate_syntax(path: str, content: str) -> dict:
    result = {"valid": True, "errors": [], "warnings": []}
    ft = _file_type(path)
    if ft == "python":
        try:
            import ast
            ast.parse(content)
        except SyntaxError as e:
            result["valid"] = False
            result["errors"].append({"line": e.lineno, "message": str(e.msg), "text": (e.text or "").strip()})
    elif ft == "json":
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            result["valid"] = False
            result["errors"].append({"line": e.lineno, "message": e.msg, "text": ""})
    elif ft == "javascript":
        ob, cb = content.count('{'), content.count('}')
        if ob != cb:
            result["warnings"].append(f"Ongelijke accolades: {ob} open, {cb} sluit")
    return result


@router.post("/files/validate")
async def validate_file(req: SaveRequest):
    """Validate syntax without saving"""
    return {"success": True, "validation": _validate_syntax(req.path, req.content)}


# ============ MODULE SANDBOX ============

class ModuleCreate(BaseModel):
    name: str
    type: str  # backend, frontend, fullstack
    description: Optional[str] = ""

class ModuleName(BaseModel):
    module_name: str

@router.get("/modules/list")
async def list_modules():
    """List all sandbox modules"""
    if not os.path.exists(SANDBOX_DIR):
        os.makedirs(SANDBOX_DIR, exist_ok=True)
        return {"success": True, "modules": []}
    modules = []
    for name in sorted(os.listdir(SANDBOX_DIR)):
        config_path = os.path.join(SANDBOX_DIR, name, "module.json")
        if os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                modules.append(json.load(f))
    return {"success": True, "modules": modules}


@router.post("/modules/create")
async def create_module(req: ModuleCreate):
    """Create new module with templates"""
    safe = req.name.lower().replace(" ", "_").replace("-", "_")
    path = os.path.join(SANDBOX_DIR, safe)
    if os.path.exists(path):
        raise HTTPException(status_code=400, detail="Module bestaat al")
    os.makedirs(path)

    config = {
        "name": safe, "display_name": req.name, "type": req.type,
        "description": req.description, "status": "sandbox",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tested": False, "integrated": False,
    }
    with open(os.path.join(path, "module.json"), 'w') as f:
        json.dump(config, f, indent=2)

    if req.type in ["backend", "fullstack"]:
        with open(os.path.join(path, f"{safe}_service.py"), 'w') as f:
            f.write(f'"""\n{req.name} Service\n"""\n\ndef hello():\n    return "{req.name} module works!"\n\ndef get_data():\n    return {{"module": "{safe}", "status": "active"}}\n\nif __name__ == "__main__":\n    print(hello())\n    print(get_data())\n')

    if req.type in ["frontend", "fullstack"]:
        comp = req.name.replace(" ", "")
        with open(os.path.join(path, f"{comp}.js"), 'w') as f:
            f.write(f'import React from "react";\n\nexport default function {comp}() {{\n  return <div className="p-6 bg-slate-800 rounded-lg"><h3 className="text-white">{req.name}</h3></div>;\n}}\n')

    return {"success": True, "message": f"Module '{req.name}' aangemaakt", "config": config}


@router.post("/modules/test")
async def test_module(req: ModuleName):
    """Test a module in safe environment"""
    path = os.path.join(SANDBOX_DIR, req.module_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Module niet gevonden")

    py_files = [f for f in os.listdir(path) if f.endswith('_service.py')]
    if not py_files:
        return {"success": False, "message": "Geen service bestand gevonden", "errors": ["Missing _service.py"]}

    svc = os.path.join(path, py_files[0])
    try:
        with open(svc, 'r') as f:
            compile(f.read(), svc, 'exec')
    except SyntaxError as e:
        return {"success": False, "message": "Syntax fout", "errors": [f"Lijn {e.lineno}: {e.msg}"]}

    try:
        r = subprocess.run(['python3', svc], capture_output=True, text=True, timeout=10, cwd=path)
        if r.returncode != 0:
            return {"success": False, "message": "Runtime fout", "errors": [r.stderr], "output": r.stdout}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Timeout", "errors": ["Module duurde te lang"]}

    config_path = os.path.join(path, "module.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    config["tested"] = True
    config["last_test"] = datetime.now(timezone.utc).isoformat()
    config["test_output"] = r.stdout
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return {"success": True, "message": "Test geslaagd!", "output": r.stdout}


@router.post("/modules/integrate")
async def integrate_module(req: ModuleName):
    """Integrate tested module into main codebase"""
    path = os.path.join(SANDBOX_DIR, req.module_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Module niet gevonden")

    config_path = os.path.join(path, "module.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    if not config.get("tested"):
        raise HTTPException(status_code=400, detail="Module moet eerst getest worden")

    integrated = []
    for fn in os.listdir(path):
        if fn.endswith('_service.py'):
            dst = os.path.join("/app/backend/modules", fn)
            shutil.copy2(os.path.join(path, fn), dst)
            integrated.append(fn)
        elif fn.endswith('.js') or fn.endswith('.jsx'):
            dst = os.path.join("/app/frontend/src/components/modules", fn)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(path, fn), dst)
            integrated.append(fn)

    config["integrated"] = True
    config["integrated_at"] = datetime.now(timezone.utc).isoformat()
    config["status"] = "integrated"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return {"success": True, "message": f"Module '{req.module_name}' geïntegreerd!", "files": integrated}


@router.delete("/modules/delete/{module_name}")
async def delete_module(module_name: str):
    """Delete module from sandbox"""
    path = os.path.join(SANDBOX_DIR, module_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Module niet gevonden")
    shutil.rmtree(path)
    return {"success": True, "message": f"Module '{module_name}' verwijderd"}
