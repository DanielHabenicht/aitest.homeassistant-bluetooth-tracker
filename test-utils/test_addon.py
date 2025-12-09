#!/usr/bin/env python3
"""Standalone tests for the Bluetooth Advertisement Monitor add-on."""
import sys
import requests
import time

ADDON_URL = "http://localhost:8099"
TIMEOUT = 5


def wait_for_addon(max_retries=20):
    """Wait for add-on to be ready."""
    print("Waiting for add-on to start...")
    for i in range(max_retries):
        try:
            response = requests.get(ADDON_URL, timeout=TIMEOUT)
            if response.status_code == 200:
                print("✓ Add-on is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
        print(f"Retry {i+1}/{max_retries}...")
    return False


def test_web_interface():
    """Test web interface."""
    print("\nTesting web interface...")
    response = requests.get(ADDON_URL, timeout=TIMEOUT)
    assert response.status_code == 200
    assert "Bluetooth Advertisement Monitor" in response.text
    print("✓ Web interface is accessible")


def test_api_endpoint():
    """Test API endpoint."""
    print("\nTesting API endpoint...")
    response = requests.get(f"{ADDON_URL}/api/advertisements", timeout=TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    print(f"✓ API endpoint returns valid JSON (found {len(data)} devices)")


def test_api_data_structure():
    """Test API data structure."""
    print("\nTesting API data structure...")
    response = requests.get(f"{ADDON_URL}/api/advertisements", timeout=TIMEOUT)
    data = response.json()
    
    if not data:
        print("⚠ No devices detected (this is OK if no Bluetooth devices nearby)")
        return
    
    # Check first device structure
    device_addr = next(iter(data.keys()))
    device = data[device_addr]
    
    required_fields = ["address", "name", "rssi", "last_seen"]
    for field in required_fields:
        assert field in device, f"Missing required field: {field}"
    
    print(f"✓ API data structure is correct")
    print(f"  Sample device: {device['name']} ({device['address']}) at {device['rssi']} dBm")


def test_hex_ascii_conversion():
    """Test HEX to ASCII conversion."""
    print("\nTesting HEX to ASCII conversion...")
    response = requests.get(f"{ADDON_URL}/api/advertisements", timeout=TIMEOUT)
    data = response.json()
    
    if not data:
        print("⚠ No devices with data detected (skipping conversion test)")
        return
    
    found_data = False
    for device_addr, device in data.items():
        if device.get("manufacturer_data"):
            for company_id, mfg_data in device["manufacturer_data"].items():
                assert "hex" in mfg_data
                assert "ascii" in mfg_data
                print(f"✓ Manufacturer data has HEX/ASCII conversion")
                print(f"  Company {company_id}: {mfg_data['hex']} -> {mfg_data['ascii']}")
                found_data = True
                break
        
        if device.get("service_data"):
            for uuid, svc_data in device["service_data"].items():
                assert "hex" in svc_data
                assert "ascii" in svc_data
                print(f"✓ Service data has HEX/ASCII conversion")
                print(f"  UUID {uuid}: {svc_data['hex']} -> {svc_data['ascii']}")
                found_data = True
                break
        
        if found_data:
            break
    
    if not found_data:
        print("⚠ No devices with manufacturer/service data (skipping conversion test)")


def main():
    """Run add-on tests."""
    print("=" * 60)
    print("Bluetooth Advertisement Monitor Add-on Tests")
    print("=" * 60)
    
    if not wait_for_addon():
        print("✗ Add-on failed to start")
        sys.exit(1)
    
    try:
        test_web_interface()
        test_api_endpoint()
        test_api_data_structure()
        test_hex_ascii_conversion()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
