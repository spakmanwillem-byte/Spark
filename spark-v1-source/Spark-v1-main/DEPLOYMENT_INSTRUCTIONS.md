# CRITICAL DEPLOYMENT INSTRUCTIONS

## Current Build Info
- **Build Date:** 2026-03-31
- **JS File:** Check `/app/frontend/build/static/js/main.*.js`
- **CSS File:** Check `/app/frontend/build/static/css/main.*.css`

## Problem
Production is serving OLD cached index.html that references non-existent files:
- OLD: `main.7e4afc08.js` ❌ (404 error)
- NEW: Check actual filename in build folder ✅

## Solution Steps

### 1. Verify Current Build (In Dev Pod)
```bash
cd /app/frontend
ls build/static/js/main.*.js
ls build/static/css/main.*.css
grep -o 'main\.[a-f0-9]*\.js' build/index.html
```

All these MUST match!

### 2. Deploy Fresh Build to Production
```bash
# Commit everything
git add .
git commit -m "Fresh build + all fixes"

# Deploy via Emergent (FORCE REBUILD - no cache!)
```

### 3. In Production Pod - Verify Build
```bash
# Check what files exist
ls /app/frontend/build/static/js/main.*.js
ls /app/frontend/build/static/css/main.*.css

# Check what index.html references
grep -o 'main\.[a-f0-9]*\.js' /app/frontend/build/index.html

# They MUST match!
```

### 4. If Mismatch in Production - Rebuild There
```bash
cd /app/frontend
rm -rf build
yarn build
sudo supervisorctl restart backend
```

### 5. Purge Cloudflare Cache
Via Emergent dashboard or contact support:
- Purge ALL cache for `spark-foundation.emergent.host`
- Wait 60 seconds
- Hard refresh browser (Ctrl+Shift+R)

## Verification
After deployment, browser should request the NEW files (not main.7e4afc08.js).

Check in browser DevTools → Network:
- Should see: `main.[NEW_HASH].js` → HTTP 200 ✅
- NOT: `main.7e4afc08.js` → HTTP 404 ❌

## Root Cause
- Frontend build files get new hashes on each build
- index.html must reference the SAME build's hashes
- Old cached HTML + new build = 404 errors
- Solution: Ensure index.html and static files from SAME build
