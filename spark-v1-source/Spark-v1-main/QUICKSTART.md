# Spark Core 4.1 - Quick Start Guide

## 🚀 One-Click Startup

Spark Core 4.1 kan nu met één commando gestart worden op Windows, Linux, en Odroid.

---

## Linux / Odroid

### Start
```bash
./start.sh
```

### Stop
```bash
./stop.sh
```

**Eerste keer:**
- Script check automatisch of Python3, Node.js, en Yarn geïnstalleerd zijn
- Dependencies worden automatisch geïnstalleerd
- Ports (8001, 3000) worden automatisch vrijgemaakt

**Na eerste keer:**
- Start binnen seconden
- Dependencies worden geskipped (already installed)

---

## Windows

### Start
Dubbelklik op `start.bat` of run in cmd:
```cmd
start.bat
```

### Stop
Dubbelklik op `stop.bat` of run in cmd:
```cmd
stop.bat
```

**Eerste keer:**
- Script check automatisch of Python, Node.js, en Yarn geïnstalleerd zijn
- Dependencies worden automatisch geïnstalleerd
- Ports worden automatisch vrijgemaakt

---

## 📋 Prerequisites

### Windows
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Yarn** - Install: `npm install -g yarn`

### Linux / Odroid
- **Python 3.8+** - `sudo apt-get install python3 python3-pip`
- **Node.js 18+** - [Install instructions](https://github.com/nodesource/distributions)
- **Yarn** - `npm install -g yarn`

---

## 🌐 URLs na Startup

| Service | URL | Beschrijving |
|---------|-----|--------------|
| **Frontend** | http://localhost:3000 | React UI |
| **Backend** | http://localhost:8001 | FastAPI server |
| **API Docs** | http://localhost:8001/docs | Swagger UI |

---

## 🔍 Status Check

### Met Supervisor (Emergent/Production)
```bash
sudo supervisorctl status
```

### Handmatig (Development)

**Linux:**
```bash
# Backend logs
tail -f backend/backend.log

# Frontend logs
tail -f frontend/frontend.log

# Check if processes are running
ps aux | grep -E "uvicorn|node"
```

**Windows:**
```cmd
# Backend logs
type backend\backend.log

# Frontend logs
type frontend\frontend.log

# Check if processes are running
tasklist | findstr "python node"
```

---

## 🛠️ Troubleshooting

### Port already in use

**Linux:**
```bash
# Check what's using port 8001
lsof -i :8001

# Kill process
lsof -ti:8001 | xargs kill -9

# Check what's using port 3000
lsof -i :3000

# Kill process
lsof -ti:3000 | xargs kill -9
```

**Windows:**
```cmd
# Check what's using port 8001
netstat -ano | findstr ":8001"

# Kill process (replace PID with actual PID)
taskkill /F /PID <PID>

# Check what's using port 3000
netstat -ano | findstr ":3000"

# Kill process
taskkill /F /PID <PID>
```

---

### Dependencies not installing

**Linux:**
```bash
# Backend dependencies manual install
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies manual install
cd frontend
yarn install
```

**Windows:**
```cmd
# Backend dependencies manual install
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt

# Frontend dependencies manual install
cd frontend
yarn install
```

---

### Backend not starting

**Check:**
1. Is Python virtual environment activated?
2. Are dependencies installed?
3. Is port 8001 available?

**Debug:**
```bash
# Linux
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001

# Windows
cd backend
call venv\Scripts\activate.bat
uvicorn server:app --host 0.0.0.0 --port 8001
```

---

### Frontend not starting

**Check:**
1. Is Node.js installed?
2. Are dependencies installed?
3. Is port 3000 available?

**Debug:**
```bash
cd frontend
yarn start
```

---

## 🎯 Platform-Specific Notes

### Odroid (ARM)
- Use same commands as Linux
- Eerste startup kan langzamer zijn (ARM processor)
- Dependencies compilation kan langer duren

### Windows
- Run cmd as Administrator voor betere port cleanup
- Windows Defender kan startup vertragen (first time)
- Gebruik PowerShell 7+ voor betere performance

### Linux (Ubuntu/Debian)
- Gebruik supervisor voor production (automatisch in Emergent)
- Voor development: run scripts direct

---

## 📝 Advanced Usage

### Custom Ports

**Backend (default: 8001):**
```bash
# Linux
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8080

# Windows
cd backend
call venv\Scripts\activate.bat
uvicorn server:app --host 0.0.0.0 --port 8080
```

**Frontend (default: 3000):**
```bash
# Set PORT env variable before starting
PORT=3001 yarn start  # Linux
set PORT=3001 && yarn start  # Windows
```

---

### Development Mode

**Backend hot reload (auto-restart on code changes):**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend hot reload:**
Enabled by default via `yarn start`

---

### Production Mode

**Use supervisor (recommended):**
```bash
sudo supervisorctl start backend frontend
sudo supervisorctl stop backend frontend
sudo supervisorctl restart backend frontend
```

**Or use systemd services (manual setup required)**

---

## 🆘 Support

**Issues?**
1. Check logs (backend.log / frontend.log)
2. Verify prerequisites installed
3. Check ports available
4. Try manual startup (see Troubleshooting)

**Still stuck?**
- Check `/app/backend/docs/` voor extra documentatie
- Review console output voor error messages
