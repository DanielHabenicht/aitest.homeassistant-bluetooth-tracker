# Bluetooth Advertisement Monitor Add-on

This Home Assistant add-on monitors all Bluetooth advertisements in range and provides a web interface to view the data.

## Features

- **Real-time monitoring** of all Bluetooth advertisements
- **HEX to ASCII conversion** for all data fields
- **Detailed information** including:
  - Device name and address
  - RSSI (signal strength)
  - Manufacturer data
  - Service data
  - Service UUIDs
- **Auto-refreshing web interface**

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Bluetooth Advertisement Monitor" add-on
3. Start the add-on

## Configuration

The add-on has the following configuration options:

- **port**: The port for the web interface (default: 8099)
- **scan_duration**: How long to scan for advertisements in seconds (default: 10, range: 1-60)
- **scan_pause**: Pause duration between scans in seconds (default: 1, range: 1-10)
- **max_device_age**: Maximum age in seconds before removing stale devices (default: 300, range: 60-3600)

## Usage

After starting the add-on:

1. Navigate to `http://homeassistant.local:8099` (or your Home Assistant IP address with the configured port)
2. The page will automatically refresh every 2 seconds
3. All Bluetooth devices in range will be displayed with their advertisement data
4. Data is shown in both HEX and ASCII formats for easy analysis

## Notes

- This add-on requires Bluetooth hardware on your Home Assistant host
- The add-on uses host network mode to access Bluetooth
- All detected advertisements are stored temporarily in memory
