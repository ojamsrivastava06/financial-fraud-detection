"""
Verification script for active live servers over TCP.
Queries localhost:8000 and localhost:8501 over network sockets to confirm runtime availability.
"""

import urllib.request
import json

def test_live_servers():
    print("=" * 70)
    print("LIVE RUNNING SERVERS HEALTH AUDIT")
    print("=" * 70)

    # 1. Test GET http://localhost:8000/health
    try:
        req = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
        body = json.loads(req.read().decode('utf-8'))
        print(f"1. http://localhost:8000/health -> Status: {req.status}")
        print(f"   Payload: {json.dumps(body, indent=2)}")
        assert req.status == 200, f"Expected 200, got {req.status}"
        assert body.get("status") == "healthy"
    except Exception as e:
        print(f"1. http://localhost:8000/health FAILED: {e}")
        raise e

    # 2. Test GET http://localhost:8000/ready
    try:
        req = urllib.request.urlopen("http://localhost:8000/ready", timeout=5)
        body = json.loads(req.read().decode('utf-8'))
        print(f"\n2. http://localhost:8000/ready -> Status: {req.status}")
        print(f"   Payload: {json.dumps(body, indent=2)}")
        assert req.status == 200, f"Expected 200, got {req.status}"
        assert body.get("status") == "ready"
    except Exception as e:
        print(f"2. http://localhost:8000/ready FAILED: {e}")
        raise e

    # 3. Test GET http://localhost:8000/docs
    try:
        req = urllib.request.urlopen("http://localhost:8000/docs", timeout=5)
        html_preview = req.read().decode('utf-8')[:200]
        print(f"\n3. http://localhost:8000/docs -> Status: {req.status}")
        print(f"   Content-Type: {req.headers.get('Content-Type')}")
        assert req.status == 200, f"Expected 200, got {req.status}"
    except Exception as e:
        print(f"3. http://localhost:8000/docs FAILED: {e}")
        raise e

    # 4. Test GET http://localhost:8501 (Streamlit Web UI)
    try:
        req = urllib.request.urlopen("http://localhost:8501", timeout=5)
        print(f"\n4. http://localhost:8501 (Streamlit UI) -> Status: {req.status}")
        print(f"   Content-Type: {req.headers.get('Content-Type')}")
        assert req.status == 200, f"Expected 200, got {req.status}"
    except Exception as e:
        print(f"4. http://localhost:8501 FAILED: {e}")
        raise e

    print("\n" + "=" * 70)
    print("ALL LIVE NETWORK ENDPOINTS VERIFIED & FUNCTIONING WITH HTTP 200.")
    print("=" * 70)

if __name__ == "__main__":
    test_live_servers()
