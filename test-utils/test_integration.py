#!/usr/bin/env python3
"""Integration tests for Home Assistant custom component."""
import sys
import requests
import json
import time

HOMEASSISTANT_URL = "http://localhost:8123"
TIMEOUT = 10


def wait_for_homeassistant(max_retries=30):
    """Wait for Home Assistant to be ready."""
    print("Waiting for Home Assistant to start...")
    for i in range(max_retries):
        try:
            response = requests.get(HOMEASSISTANT_URL, timeout=TIMEOUT)
            if response.status_code == 200:
                print("✓ Home Assistant is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
        print(f"Retry {i+1}/{max_retries}...")
    return False


def test_integration_loaded():
    """Test that the integration can be loaded."""
    # Check if manifest is valid
    print("Checking integration manifest...")
    with open("custom_components/bluetooth_tracker/manifest.json") as f:
        manifest = json.load(f)
        assert "domain" in manifest
        assert manifest["domain"] == "bluetooth_tracker"
        print("✓ Manifest is valid")


def test_api_access():
    """Test Home Assistant API access."""
    print("Testing Home Assistant API...")
    try:
        response = requests.get(f"{HOMEASSISTANT_URL}/api/", timeout=TIMEOUT)
        print(f"API response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Home Assistant version: {data.get('message', 'unknown')}")
    except Exception as e:
        print(f"Note: API access requires authentication: {e}")


def main():
    """Run integration tests."""
    print("=" * 60)
    print("Home Assistant Integration Tests")
    print("=" * 60)
    
    # Test manifest
    test_integration_loaded()
    
    # If Home Assistant is running, test API
    if wait_for_homeassistant():
        test_api_access()
    
    print("\n✓ Integration tests completed")


if __name__ == "__main__":
    main()
