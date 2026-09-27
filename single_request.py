import httpx
import time

with open("pgiff.webp", "rb") as f:
    img = f.read()

files = {'file': ("pgiff.webp", img, "img/webp")}
url = "http://127.0.0.1:8001/"

print("Sending single request...")
start = time.perf_counter()

try:
    response = httpx.post(url, files=files, timeout=10)
    end = time.perf_counter()
    print(f"Response: {response.status_code}")
    print(f"Body: {response.text}")
    print(f"Time: {end - start:.2f}s")
except Exception as e:
    end = time.perf_counter()
    print(f"ERROR: {type(e).__name__}: {e}")
    print(f"Time: {end - start:.2f}s")
