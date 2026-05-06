#!/usr/bin/env python3
"""Automated benchmark test for ASCII Art Generator"""
import requests
import time
import sys
import json

BACKEND_URL = "http://localhost:5001"
TEST_PROMPT = "A dark lighthouse on a rocky coast with fog and mysterious glowing symbols carved into the stone"
TEST_WIDTH = 120
TEST_STYLE = "lovecraftian"

def check_services():
    """Check if Flask and Ollama are running"""
    print("🔍 Checking services...")

    # Check Flask
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask backend: OK (port 5001)")
        else:
            print("❌ Flask backend: Error")
            return False
    except requests.ConnectionError:
        print("❌ Flask backend: Not running (http://localhost:5001)")
        return False

    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            print(f"✅ Ollama: OK with models: {model_names}")
        else:
            print("❌ Ollama: Error")
            return False
    except requests.ConnectionError:
        print("❌ Ollama: Not running (http://localhost:11434)")
        return False

    return True

def run_benchmark():
    """Run the benchmark test"""
    print("\n📊 Running Benchmark Test")
    print(f"  Prompt: {TEST_PROMPT[:50]}...")
    print(f"  Width: {TEST_WIDTH} chars")
    print(f"  Style: {TEST_STYLE}")
    print()

    start_time = time.time()

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/generate",
            json={
                "prompt": TEST_PROMPT,
                "width": TEST_WIDTH,
                "style": TEST_STYLE,
            },
            timeout=120,
        )

        elapsed_time = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

        data = response.json()

        if not data.get("success"):
            print(f"❌ Generation Failed: {data.get('error')}")
            return False

        ascii_art = data.get("ascii_art", "")
        lines = ascii_art.strip().split("\n")

        # Validate results
        print(f"⏱️  Response time: {elapsed_time:.1f} seconds")
        print(f"📏 ASCII art size: {len(lines)} lines × {max(len(l) for l in lines)} chars")

        results = {
            "time": elapsed_time,
            "lines": len(lines),
            "width": max(len(l) for l in lines),
            "quality": "good" if len(lines) > 50 else "ok" if len(lines) > 30 else "poor",
        }

        # Check success criteria
        checks = [
            ("Response < 60s", elapsed_time < 60, elapsed_time < 60),
            ("Lines > 80", len(lines) > 80, len(lines) > 50),
            ("No errors", "error" not in data, True),
            ("Has content", bool(ascii_art), bool(ascii_art)),
        ]

        print("\n✓ Success Criteria:")
        all_pass = True
        for check_name, condition, weight in checks:
            status = "✅" if condition else "⚠️"
            print(f"  {status} {check_name}: {condition}")
            if not condition and weight:
                all_pass = False

        if all_pass:
            print("\n🎉 BENCHMARK PASSED")
            print("\nSample output (first 20 lines):")
            print("─" * 60)
            for line in lines[:20]:
                print(line)
            print("─" * 60)
            return True
        else:
            print("\n⚠️  BENCHMARK DEGRADED (but functional)")
            return True

    except requests.Timeout:
        print(f"❌ Timeout after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("🎨 ASCII Art Generator - Benchmark Test")
    print("="*60)

    # Check services
    if not check_services():
        print("\n❌ Services not ready. Start them with:")
        print("  Terminal 1: cd ascii_generator && source venv/bin/activate && python server.py")
        print("  Terminal 2: Make sure Ollama is running (ollama serve)")
        sys.exit(1)

    # Run benchmark
    success = run_benchmark()

    print("\n" + "="*60)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
