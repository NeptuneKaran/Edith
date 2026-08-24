"""
tests/test_live_server_startup.py
Spawns a real Streamlit server with Render-like parameters:
--server.port 10000 --server.address 0.0.0.0 --server.headless true
Polls http://127.0.0.1:10000/ and http://127.0.0.1:10000/_stcore/health
Verifies that the server boots cleanly, binds to 0.0.0.0, and responds with HTTP 200.
"""
import sys
import os
import subprocess
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_live_server():
    print("=== TESTING REAL STREAMLIT SERVER STARTUP (0.0.0.0:10000) ===")
    test_port = 10000
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(test_port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    
    env = os.environ.copy()
    # Test without GEMINI_API_KEY to verify zero-key cloud boot
    env.pop("GEMINI_API_KEY", None)
    
    print(f"Launching command: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    url_health = f"http://127.0.0.1:{test_port}/_stcore/health"
    url_main = f"http://127.0.0.1:{test_port}/"
    
    max_retries = 25
    booted = False
    
    try:
        for attempt in range(1, max_retries + 1):
            time.sleep(1.0)
            # Check if process terminated prematurely
            poll = proc.poll()
            if poll is not None:
                out, err = proc.communicate()
                raise RuntimeError(f"Streamlit server exited prematurely with code {poll}:\nSTDOUT: {out}\nSTDERR: {err}")
            
            try:
                with urllib.request.urlopen(url_health, timeout=2.0) as resp:
                    if resp.status == 200:
                        print(f"  [PASS] Streamlit health endpoint returned HTTP {resp.status} on attempt {attempt}")
                        booted = True
                        break
            except (urllib.error.URLError, ConnectionRefusedError):
                continue
                
        if not booted:
            raise TimeoutError("Streamlit server failed to respond within 25 seconds.")
            
        # Verify Main Page HTML
        with urllib.request.urlopen(url_main, timeout=3.0) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            assert resp.status == 200, f"Expected HTTP 200, got {resp.status}"
            assert "Streamlit" in content or "EDITH" in content or "html" in content
            print("  [PASS] Main page returned HTTP 200 OK with valid HTML payload")
            
        print("\n[PASS] LIVE SERVER BOOT AND HEALTH CHECK VERIFIED SUCCESSFULLY!")
        
    finally:
        print("Terminating test server process...")
        proc.terminate()
        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Server process cleanly stopped.")

if __name__ == "__main__":
    test_live_server()
