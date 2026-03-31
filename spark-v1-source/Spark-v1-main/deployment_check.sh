#!/bin/bash
echo "=================================================="
echo "DEPLOYMENT VERIFICATION SCRIPT"
echo "=================================================="
echo ""

echo "1. Backend Health Check:"
curl -s http://localhost:8001/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   Status: {d.get(\"status\", \"ERROR\")}')" 2>/dev/null || echo "   ❌ Health check failed"
echo ""

echo "2. Index.html References:"
echo "   JS file:"
curl -s http://localhost:8001/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.js' | head -n 1 | sed 's/^/      /'
echo "   CSS file:"
curl -s http://localhost:8001/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.css' | head -n 1 | sed 's/^/      /'
echo ""

echo "3. Build Directory Contents:"
echo "   JS files:"
ls /app/frontend/build/static/js/main.*.js 2>/dev/null | xargs -n1 basename | sed 's/^/      /' || echo "      ❌ No JS files found"
echo "   CSS files:"
ls /app/frontend/build/static/css/main.*.css 2>/dev/null | xargs -n1 basename | sed 's/^/      /' || echo "      ❌ No CSS files found"
echo ""

echo "4. Static File Serving Test:"
JS_FILE=$(curl -s http://localhost:8001/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.js' | head -n 1)
CSS_FILE=$(curl -s http://localhost:8001/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.css' | head -n 1)

if [ -n "$JS_FILE" ]; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/static/js/$JS_FILE")
    echo "   /static/js/$JS_FILE → HTTP $STATUS"
    if [ "$STATUS" != "200" ]; then
        echo "      ❌ FILE NOT SERVED!"
    fi
fi

if [ -n "$CSS_FILE" ]; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/static/css/$CSS_FILE")
    echo "   /static/css/$CSS_FILE → HTTP $STATUS"
    if [ "$STATUS" != "200" ]; then
        echo "      ❌ FILE NOT SERVED!"
    fi
fi

echo ""
echo "5. File Consistency Check:"
INDEX_JS=$(curl -s http://localhost:8001/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.js' | head -n 1)
ACTUAL_JS=$(ls /app/frontend/build/static/js/main.*.js 2>/dev/null | xargs -n1 basename | head -n 1)

if [ "$INDEX_JS" == "$ACTUAL_JS" ]; then
    echo "   ✅ JS files MATCH"
else
    echo "   ❌ MISMATCH!"
    echo "      Index.html wants: $INDEX_JS"
    echo "      Build contains:   $ACTUAL_JS"
fi

INDEX_CSS=$(curl -s http://localhost:8001/ 2>/dev/null | grep -o 'main\.[a-f0-9]*\.css' | head -n 1)
ACTUAL_CSS=$(ls /app/frontend/build/static/css/main.*.css 2>/dev/null | xargs -n1 basename | head -n 1)

if [ "$INDEX_CSS" == "$ACTUAL_CSS" ]; then
    echo "   ✅ CSS files MATCH"
else
    echo "   ❌ MISMATCH!"
    echo "      Index.html wants: $INDEX_CSS"
    echo "      Build contains:   $ACTUAL_CSS"
fi

echo ""
echo "=================================================="
echo "END OF VERIFICATION"
echo "=================================================="
