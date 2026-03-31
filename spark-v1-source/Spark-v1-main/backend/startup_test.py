#!/usr/bin/env python3
"""
Startup Test Script - Verifies backend can start quickly
Run this before deployment to ensure no blocking imports
"""
import time
import sys

print("=" * 60)
print("BACKEND STARTUP TEST")
print("=" * 60)
print()

# Test 1: Import time
print("Test 1: Measuring import time...")
start = time.time()
sys.path.insert(0, '/app/backend')
import server
elapsed = time.time() - start
print(f"   Import time: {elapsed:.2f}s")
if elapsed > 5:
    print(f"   ❌ FAIL: Import took {elapsed:.2f}s (should be < 5s)")
    sys.exit(1)
else:
    print(f"   ✅ PASS: Import completed in {elapsed:.2f}s")

print()

# Test 2: Check lazy loading
print("Test 2: Verifying lazy loading...")
from services.nlp_service import NLPService
from services.entity_service import EntityService

nlp_service = NLPService()
entity_service = EntityService()

# Should NOT have loaded spaCy yet
if hasattr(nlp_service, '_nlp') and nlp_service._nlp is None:
    print("   ✅ PASS: NLPService uses lazy loading")
else:
    print("   ❌ FAIL: NLPService loaded spaCy during __init__")
    sys.exit(1)

if hasattr(entity_service, '_nlp') and entity_service._nlp is None:
    print("   ✅ PASS: EntityService uses lazy loading")
else:
    print("   ❌ FAIL: EntityService loaded spaCy during __init__")
    sys.exit(1)

print()

# Test 3: Health endpoint
print("Test 3: Checking health endpoint...")
if hasattr(server.app, 'routes'):
    health_routes = [r for r in server.app.routes if '/health' in str(r.path)]
    if health_routes:
        print(f"   ✅ PASS: Found {len(health_routes)} health endpoint(s)")
    else:
        print("   ❌ FAIL: No /health endpoint found")
        sys.exit(1)
else:
    print("   ⚠️  SKIP: Cannot verify routes")

print()
print("=" * 60)
print("✅ ALL TESTS PASSED - Backend ready for deployment")
print("=" * 60)
