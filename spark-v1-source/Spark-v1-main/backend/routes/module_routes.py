"""
Module Sandbox Routes
Veilige omgeving voor module development en testing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import subprocess
import shutil
from datetime import datetime

router = APIRouter()

SANDBOX_DIR = "/app/backend/sandbox/modules"
BACKEND_DIR = "/app/backend"
FRONTEND_DIR = "/app/frontend/src"


class ModuleCreateRequest(BaseModel):
    name: str
    type: str  # "backend", "frontend", "fullstack"
    description: Optional[str] = ""


class ModuleTestRequest(BaseModel):
    module_name: str


class ModuleIntegrateRequest(BaseModel):
    module_name: str


@router.get("/list")
async def list_modules():
    """List all modules in sandbox"""
    try:
        if not os.path.exists(SANDBOX_DIR):
            return {"success": True, "modules": []}
        
        modules = []
        for module_name in os.listdir(SANDBOX_DIR):
            module_path = os.path.join(SANDBOX_DIR, module_name)
            if os.path.isdir(module_path):
                # Check for config
                config_path = os.path.join(module_path, "module.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        modules.append(config)
        
        return {"success": True, "modules": modules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_module(req: ModuleCreateRequest):
    """Create new module with templates"""
    try:
        # Sanitize name
        safe_name = req.name.lower().replace(" ", "_").replace("-", "_")
        module_path = os.path.join(SANDBOX_DIR, safe_name)
        
        if os.path.exists(module_path):
            raise HTTPException(status_code=400, detail="Module already exists")
        
        os.makedirs(module_path)
        
        # Create module config
        config = {
            "name": safe_name,
            "display_name": req.name,
            "type": req.type,
            "description": req.description,
            "status": "sandbox",
            "created_at": datetime.now().isoformat(),
            "tested": False,
            "integrated": False
        }
        
        with open(os.path.join(module_path, "module.json"), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create templates based on type
        if req.type in ["backend", "fullstack"]:
            # Python service template
            python_template = f'''"""
{req.name} Service
Auto-generated module template
"""

def hello():
    """Test function"""
    return "{req.name} module works!"


def get_data():
    """Example data function"""
    return {{
        "module": "{safe_name}",
        "status": "active",
        "message": "Module is working correctly"
    }}


if __name__ == "__main__":
    # Test the module
    print(hello())
    print(get_data())
'''
            with open(os.path.join(module_path, f"{safe_name}_service.py"), 'w') as f:
                f.write(python_template)
            
            # Python route template
            route_template = f'''"""
{req.name} Routes
Auto-generated API routes
"""
from fastapi import APIRouter
from services.{safe_name}_service import hello, get_data

router = APIRouter()


@router.get("/hello")
async def get_hello():
    """Test endpoint"""
    return {{"message": hello()}}


@router.get("/data")
async def get_module_data():
    """Get module data"""
    return get_data()
'''
            with open(os.path.join(module_path, f"{safe_name}_routes.py"), 'w') as f:
                f.write(route_template)
        
        if req.type in ["frontend", "fullstack"]:
            # React component template
            component_template = f'''import React, {{ useState }} from 'react';

function {req.name.replace(" ", "")}Component() {{
  const [data, setData] = useState(null);
  
  const loadData = async () => {{
    try {{
      const response = await fetch(`${{process.env.REACT_APP_BACKEND_URL}}/api/{safe_name}/data`);
      const result = await response.json();
      setData(result);
    }} catch (error) {{
      console.error('Error loading data:', error);
    }}
  }};
  
  return (
    <div className="p-6 bg-slate-800 rounded-lg">
      <h3 className="text-xl font-bold text-white mb-4">
        {req.name}
      </h3>
      <p className="text-gray-400 mb-4">
        {req.description or "Module component"}
      </p>
      
      <button 
        onClick={{loadData}}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Load Data
      </button>
      
      {{data && (
        <pre className="mt-4 p-4 bg-slate-700 rounded text-sm text-gray-300">
          {{JSON.stringify(data, null, 2)}}
        </pre>
      )}}
    </div>
  );
}}

export default {req.name.replace(" ", "")}Component;
'''
            with open(os.path.join(module_path, f"{req.name.replace(' ', '')}.js"), 'w') as f:
                f.write(component_template)
        
        # Create README
        readme = f'''# {req.name}

{req.description}

## Status: Sandbox

Deze module is nog in ontwikkeling en test fase.

## Files:
'''
        for file in os.listdir(module_path):
            if file != "README.md":
                readme += f"- {file}\n"
        
        with open(os.path.join(module_path, "README.md"), 'w') as f:
            f.write(readme)
        
        return {
            "success": True,
            "message": f"Module '{req.name}' created successfully",
            "module_path": f"/sandbox/modules/{safe_name}",
            "config": config
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_module(req: ModuleTestRequest):
    """Test module in safe environment"""
    try:
        module_path = os.path.join(SANDBOX_DIR, req.module_name)
        
        if not os.path.exists(module_path):
            raise HTTPException(status_code=404, detail="Module not found")
        
        # Find Python file
        python_files = [f for f in os.listdir(module_path) if f.endswith('_service.py')]
        
        if not python_files:
            return {
                "success": False,
                "message": "No Python service file found",
                "errors": ["Missing _service.py file"]
            }
        
        service_file = os.path.join(module_path, python_files[0])
        
        # Test 1: Syntax check
        try:
            with open(service_file, 'r') as f:
                code = f.read()
            compile(code, service_file, 'exec')
        except SyntaxError as e:
            return {
                "success": False,
                "message": "Syntax error in Python code",
                "errors": [f"Line {e.lineno}: {e.msg}"]
            }
        
        # Test 2: Import check
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', service_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "Compilation failed",
                    "errors": [result.stderr]
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Test timeout",
                "errors": ["Module took too long to compile"]
            }
        
        # Test 3: Execute test
        try:
            result = subprocess.run(
                ['python3', service_file],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=module_path
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "Runtime error",
                    "errors": [result.stderr],
                    "output": result.stdout
                }
            
            # Update config
            config_path = os.path.join(module_path, "module.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            config['tested'] = True
            config['last_test'] = datetime.now().isoformat()
            config['test_output'] = result.stdout
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                "success": True,
                "message": "✅ Module test passed!",
                "output": result.stdout,
                "can_integrate": True
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Execution timeout",
                "errors": ["Module took too long to execute"]
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": "Test failed",
            "errors": [str(e)]
        }


@router.post("/integrate")
async def integrate_module(req: ModuleIntegrateRequest):
    """Integrate tested module into main codebase"""
    try:
        module_path = os.path.join(SANDBOX_DIR, req.module_name)
        
        if not os.path.exists(module_path):
            raise HTTPException(status_code=404, detail="Module not found")
        
        # Check if tested
        config_path = os.path.join(module_path, "module.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if not config.get('tested'):
            raise HTTPException(status_code=400, detail="Module must be tested first")
        
        # Integration logic
        integrated_files = []
        
        # Move Python files
        for file in os.listdir(module_path):
            if file.endswith('_service.py'):
                src = os.path.join(module_path, file)
                dst = os.path.join(BACKEND_DIR, 'services', file)
                shutil.copy2(src, dst)
                integrated_files.append(f"services/{file}")
            
            elif file.endswith('_routes.py'):
                src = os.path.join(module_path, file)
                dst = os.path.join(BACKEND_DIR, 'routes', file)
                shutil.copy2(src, dst)
                integrated_files.append(f"routes/{file}")
            
            elif file.endswith('.js') or file.endswith('.jsx'):
                src = os.path.join(module_path, file)
                dst = os.path.join(FRONTEND_DIR, 'components', file)
                shutil.copy2(src, dst)
                integrated_files.append(f"components/{file}")
        
        # Update config
        config['integrated'] = True
        config['integrated_at'] = datetime.now().isoformat()
        config['integrated_files'] = integrated_files
        config['status'] = 'integrated'
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "success": True,
            "message": f"✅ Module '{req.module_name}' integrated successfully!",
            "integrated_files": integrated_files,
            "note": "Restart backend/frontend om module te activeren"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{module_name}")
async def delete_module(module_name: str):
    """Delete module from sandbox"""
    try:
        module_path = os.path.join(SANDBOX_DIR, module_name)
        
        if not os.path.exists(module_path):
            raise HTTPException(status_code=404, detail="Module not found")
        
        shutil.rmtree(module_path)
        
        return {
            "success": True,
            "message": f"Module '{module_name}' deleted"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
