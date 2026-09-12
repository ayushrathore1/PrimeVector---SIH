"""Quick test: Can httpx reach the Colab tunnel?"""
import asyncio
import httpx

COLAB_URL = "https://smasher-fernlike-trough.ngrok-free.dev"

async def test():
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        headers={"ngrok-skip-browser-warning": "true"},
    )
    
    # Test 1: Health check via tunnel
    print("=== Test 1: Health Check ===")
    try:
        r = await client.get(f"{COLAB_URL}/feat/healthz")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Test 2: Feature extraction
    print("\n=== Test 2: Feature Extraction ===")
    import base64
    audio_b64 = base64.b64encode(b'\x00' * 32000).decode()
    payload = {
        "request_id": "test-httpx",
        "tenant_id": "qa",
        "audio_bytes": audio_b64,
        "sample_rate_hz": 16000,
        "channels": 1,
    }
    try:
        r = await client.post(f"{COLAB_URL}/feat/v1/extract", json=payload)
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type', 'N/A')}")
        if r.status_code == 200:
            data = r.json()
            print(f"  duration_ms: {data.get('duration_ms')}")
            print(f"  embedding length: {len(data.get('speaker_embedding', []))}")
        else:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
    
    await client.aclose()

asyncio.run(test())
