#!/usr/bin/env python3
"""Test runner for Home Assistant Bluetooth Tracker."""
import sys
import time
import requests
from typing import Dict, Any

# Test configuration
HOMEASSISTANT_URL = "http://homeassistant-test:8123"
ADDON_URL = "http://addon-test:8099"
TIMEOUT = 5


class TestRunner:
    """Test runner for both projects."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test(self, name: str, func):
        """Run a test function."""
        try:
            print(f"Running test: {name}...", end=" ")
            func()
            print("✓ PASSED")
            self.passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            self.failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.failed += 1

    def test_addon_web_interface(self):
        """Test that add-on web interface is accessible."""
        response = requests.get(ADDON_URL, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "Bluetooth Advertisement Monitor" in response.text, "Expected page title not found"

    def test_addon_api_endpoint(self):
        """Test that add-on API endpoint returns JSON."""
        response = requests.get(f"{ADDON_URL}/api/advertisements", timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Expected dictionary response"

    def test_homeassistant_accessible(self):
        """Test that Home Assistant is accessible."""
        response = requests.get(HOMEASSISTANT_URL, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_addon_api_structure(self):
        """Test that add-on API returns proper structure."""
        response = requests.get(f"{ADDON_URL}/api/advertisements", timeout=TIMEOUT)
        data = response.json()
        # Should be a dict (may be empty if no devices detected)
        assert isinstance(data, dict), "Expected dictionary"
        # If there are devices, check structure
        for device_addr, device_data in data.items():
            assert "address" in device_data, "Device missing address"
            assert "name" in device_data, "Device missing name"
            assert "rssi" in device_data, "Device missing rssi"
            assert "last_seen" in device_data, "Device missing last_seen"
            break  # Just check first device

    def test_addon_hex_to_ascii_conversion(self):
        """Test HEX to ASCII conversion in add-on."""
        # This is tested implicitly by the structure test
        # The conversion happens in the backend and is displayed in the UI
        response = requests.get(f"{ADDON_URL}/api/advertisements", timeout=TIMEOUT)
        data = response.json()
        for device_addr, device_data in data.items():
            if device_data.get("manufacturer_data"):
                for company_id, mfg_data in device_data["manufacturer_data"].items():
                    assert "hex" in mfg_data, "Manufacturer data missing hex"
                    assert "ascii" in mfg_data, "Manufacturer data missing ascii"
                    break
            if device_data.get("service_data"):
                for uuid, svc_data in device_data["service_data"].items():
                    assert "hex" in svc_data, "Service data missing hex"
                    assert "ascii" in svc_data, "Service data missing ascii"
                    break
            break

    def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("Running Bluetooth Tracker Tests")
        print("=" * 60)
        print()

        # Give services a moment to fully start
        print("Waiting for services to stabilize...")
        time.sleep(5)

        # Run tests
        print("\n--- Add-on Tests ---")
        self.test("Add-on web interface accessible", self.test_addon_web_interface)
        self.test("Add-on API endpoint accessible", self.test_addon_api_endpoint)
        self.test("Add-on API structure valid", self.test_addon_api_structure)
        self.test("Add-on HEX to ASCII conversion", self.test_addon_hex_to_ascii_conversion)

        print("\n--- Home Assistant Tests ---")
        self.test("Home Assistant accessible", self.test_homeassistant_accessible)

        # Summary
        print("\n" + "=" * 60)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        print("=" * 60)

        return self.failed == 0


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
