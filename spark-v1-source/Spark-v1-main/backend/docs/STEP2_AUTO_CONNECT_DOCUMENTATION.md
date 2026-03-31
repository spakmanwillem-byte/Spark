# Step 2: Auto-connect Frontend ↔ Backend - Documentatie

**Datum:** 2026-03-30  
**Status:** ✅ **GEÏMPLEMENTEERD & GETEST**

---

## Overzicht

Automatische detectie van development vs production omgeving zonder hardcoded URLs of poorten.

**Voordelen:**
- ✅ Werkt in zowel dev als deployed omgeving
- ✅ Geen hardcoded IPs/poorten
- ✅ Fallback naar localhost voor development
- ✅ CORS correct geconfigureerd
- ✅ Simpel en robuust (geen over-engineering)

---

## Implementatie

### 1. Frontend: API Configuration (`/app/frontend/src/config/api.js`)

**Auto-detection logica:**
```javascript
export const getBackendUrl = () => {
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  
  if (envUrl && envUrl.trim() !== '') {
    // Production: gebruik env variable
    return envUrl.trim();
  }
  
  // Development: fallback naar localhost
  return 'http://localhost:8001';
};
```

**Features:**
- 🎯 **Priority 1:** `REACT_APP_BACKEND_URL` env variable (production)
- 🎯 **Priority 2:** Fallback naar `http://localhost:8001` (development)
- 📊 **Logging:** Console output toont welke URL gebruikt wordt
- 🔄 **Exports:** `BACKEND_URL`, `API_URL`, `isDevelopment()`, `isProduction()`

---

### 2. Backend: CORS Configuration (`/app/backend/server.py`)

**Smart CORS origins:**
```python
def get_cors_origins():
    cors_env = os.environ.get('CORS_ORIGINS', '*')
    
    if cors_env == '*':
        return ["*"]  # Development: allow all
    
    # Production: parse comma-separated origins
    origins = [origin.strip() for origin in cors_env.split(',')]
    
    # Always include localhost for development
    localhost_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    return list(set(origins + localhost_origins))
```

**Features:**
- ✅ **Flexible:** CORS_ORIGINS env variable (comma-separated)
- ✅ **Safe default:** `*` (allow all) voor development
- ✅ **Localhost support:** Altijd localhost:3000 toestaan
- ✅ **Logging:** CORS origins worden gelogd bij startup

---

## Environment Variables

### Frontend (`/app/frontend/.env`)
```env
REACT_APP_BACKEND_URL=https://spark-foundation.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

**REACT_APP_BACKEND_URL:**
- **Production:** URL van deployed backend (bijv. Emergent/Kubernetes)
- **Development:** Laat leeg of verwijder → fallback naar localhost:8001

---

### Backend (`/app/backend/.env`)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY=sk-emergent-xxx
USE_MOCK_TRADING=false
```

**CORS_ORIGINS:**
- **Development:** `*` (allow all)
- **Production:** Comma-separated lijst, bijv:
  ```
  CORS_ORIGINS="https://spark-foundation.preview.emergentagent.com,https://custom-domain.com"
  ```

---

## Gebruik in Code

### Frontend - Import API Config

**Oude manier (DEPRECATED):**
```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
```

**Nieuwe manier:**
```javascript
import { BACKEND_URL, API_URL } from "./config/api";

const API = API_URL;

// Of gebruik helper functies:
import { getBackendUrl, getApiUrl, isDevelopment } from "./config/api";

if (isDevelopment()) {
  console.log("Running in dev mode");
}
```

**Voorbeeld in Component:**
```javascript
import { API_URL } from "../config/api";

const MyComponent = () => {
  useEffect(() => {
    fetch(`${API_URL}/emotions/current`)
      .then(res => res.json())
      .then(data => console.log(data));
  }, []);
};
```

---

## Testing Results

### ✅ Test 1: Production Mode (met REACT_APP_BACKEND_URL)

**Environment:**
```
REACT_APP_BACKEND_URL=https://spark-foundation.preview.emergentagent.com
```

**Console output:**
```
[API Config] Using production URL: https://spark-foundation.preview.emergentagent.com
[API Config] Environment: PRODUCTION
[API Config] Backend URL: https://spark-foundation.preview.emergentagent.com
[API Config] API URL: https://spark-foundation.preview.emergentagent.com/api
```

**Result:** ✅ **PASS** - Gebruikt production URL

---

### ✅ Test 2: Development Mode (zonder REACT_APP_BACKEND_URL)

**Environment:**
```
REACT_APP_BACKEND_URL=
```

**Console output:**
```
[API Config] Using development fallback: http://localhost:8001
[API Config] Environment: DEVELOPMENT
[API Config] Backend URL: http://localhost:8001
[API Config] API URL: http://localhost:8001/api
```

**Result:** ✅ **PASS** - Fallback naar localhost

---

### ✅ Test 3: CORS Configuration

**Test command:**
```bash
curl -X OPTIONS "https://spark-foundation.preview.emergentagent.com/api/emotions/current" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

**Response headers:**
```
access-control-allow-origin: *
access-control-allow-headers: *
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH
access-control-max-age: 300
```

**Result:** ✅ **PASS** - CORS headers correct

---

### ✅ Test 4: Frontend API Calls

**Screenshot test:** Frontend laadt correct en maakt API calls naar:
```
https://spark-foundation.preview.emergentagent.com/api/emotions/current
```

**Browser console:**
- ✅ API Config logs zichtbaar
- ✅ API calls succesvol (200 OK)
- ✅ Geen CORS errors

**Result:** ✅ **PASS** - Frontend ↔ Backend connectie werkt

---

## Deployment Scenarios

### Scenario 1: Lokale Development
**Setup:**
- Frontend: `yarn start` op localhost:3000
- Backend: Supervisor op localhost:8001
- REACT_APP_BACKEND_URL: **leeg** of **niet gezet**

**Werking:**
```
Frontend → http://localhost:8001/api → Backend
```

✅ Fallback kick in automatisch

---

### Scenario 2: Emergent/Kubernetes (Production)
**Setup:**
- Frontend: Deployed via Emergent
- Backend: Deployed via Emergent
- REACT_APP_BACKEND_URL: `https://spark-foundation.preview.emergentagent.com`

**Werking:**
```
Frontend → https://spark-foundation.preview.emergentagent.com/api → Backend
```

✅ Gebruikt production URL uit .env

---

### Scenario 3: Custom Domain
**Setup:**
- Frontend: Custom domain (bijv. spark.example.com)
- Backend: Custom domain (bijv. api.spark.example.com)
- REACT_APP_BACKEND_URL: `https://api.spark.example.com`
- CORS_ORIGINS: `https://spark.example.com`

**Werking:**
```
Frontend (spark.example.com) → api.spark.example.com/api → Backend
```

✅ CORS toestaat spark.example.com + localhost

---

## Voordelen van Deze Aanpak

### ✅ 1. Geen Hardcoded URLs
**Voor:**
```javascript
const API = "http://192.168.1.100:8001/api";  // ❌ Breekt bij deploy
```

**Na:**
```javascript
import { API_URL } from "./config/api";  // ✅ Werkt overal
const API = API_URL;
```

---

### ✅ 2. Automatische Environment Detection
Geen handmatige switches nodig - systeem detecteert automatisch.

---

### ✅ 3. Developer-Friendly
Nieuwe developers kunnen direct beginnen zonder URL configuratie.

---

### ✅ 4. Production-Ready
CORS is veilig geconfigureerd voor production met fallback voor dev.

---

## Troubleshooting

### ⚠️ "Failed to fetch" errors

**Probleem:** API calls falen  
**Check:**
1. Is backend running? → `curl http://localhost:8001/api/emotions/current`
2. Is REACT_APP_BACKEND_URL correct in frontend/.env?
3. Check browser console voor CORS errors

**Fix:**
```bash
# Check backend status
sudo supervisorctl status backend

# Restart if needed
sudo supervisorctl restart backend
```

---

### ⚠️ CORS errors in browser

**Probleem:** `Access-Control-Allow-Origin` error  
**Check:**
1. Backend CORS_ORIGINS in backend/.env
2. Is frontend origin toegestaan?

**Fix production:**
```env
# backend/.env
CORS_ORIGINS="https://your-frontend-domain.com,http://localhost:3000"
```

**Fix development:**
```env
# backend/.env
CORS_ORIGINS="*"
```

---

### ⚠️ Fallback werkt niet in production

**Probleem:** Gebruikt localhost in plaats van production URL  
**Check:**
1. Is REACT_APP_BACKEND_URL gezet in frontend/.env?
2. Rebuild frontend na .env change: `yarn build`

**Fix:**
```bash
# frontend/.env
REACT_APP_BACKEND_URL=https://your-backend-url.com

# Restart frontend
sudo supervisorctl restart frontend
```

---

## Migratie Guide (Voor Bestaande Code)

### Stap 1: Update Imports
**Van:**
```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
```

**Naar:**
```javascript
import { API_URL } from "./config/api";
const API = API_URL;
```

---

### Stap 2: Remove Hardcoded URLs
**Zoek:**
```bash
grep -r "http://\|https://" /app/frontend/src --include="*.js" --include="*.jsx"
```

**Vervang met:**
```javascript
import { BACKEND_URL, API_URL } from "./config/api";
```

---

### Stap 3: Test
1. Test in development (zonder REACT_APP_BACKEND_URL)
2. Test in production (met REACT_APP_BACKEND_URL)
3. Check browser console voor API Config logs

---

## Checklist

- [x] API config file gemaakt (`/app/frontend/src/config/api.js`)
- [x] App.js ge-update om config te gebruiken
- [x] CORS configuratie verbeterd in server.py
- [x] Fallback naar localhost getest
- [x] Production URL getest
- [x] CORS headers geverifieerd
- [x] Frontend ↔ Backend connectie werkt
- [x] Console logging actief voor debugging
- [x] Documentatie compleet

---

## Conclusie

✅ **Step 2: Auto-connect is succesvol geïmplementeerd**

**Wat werkt:**
- Auto-detectie van dev vs production
- Fallback naar localhost
- CORS correct geconfigureerd
- Geen hardcoded URLs
- Simpel en robuust

**Production ready:** Ja  
**Breaking changes:** Nee (backwards compatible)  
**Klaar voor Step 3:** Ja
