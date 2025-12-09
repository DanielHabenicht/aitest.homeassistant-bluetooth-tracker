# Bluetooth Tracker Integration

This Home Assistant integration automatically tracks Bluetooth devices by monitoring Bluetooth advertisements.

## Features

- **Automatic device discovery**: Entities are created automatically when Bluetooth advertisements are detected
- **Device tracking**: Each discovered Bluetooth device gets its own device tracker entity
- **Real-time updates**: Entities update when new advertisements are received
- **Rich attributes**: Each entity includes:
  - Device address
  - RSSI (signal strength)
  - Device name (if available)

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Search for "Bluetooth Tracker" in HACS
3. Install the integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/bluetooth_tracker` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Bluetooth Tracker"
4. Click on "Bluetooth Tracker" to add it
5. The integration will start tracking all Bluetooth devices automatically

## Usage

Once configured, the integration will:

1. Listen for all Bluetooth advertisements
2. Automatically create device tracker entities for each discovered device
3. Update entities when new advertisements are received

## Entity Naming

Entities are named based on the device's Bluetooth address:
- Entity ID: `device_tracker.bluetooth_tracker_XX_XX_XX_XX_XX_XX`
- Friendly name: Device's advertised name or "Bluetooth Device [address]"

## State Attributes

Each device tracker entity provides the following attributes:

- `address`: The Bluetooth MAC address
- `rssi`: Signal strength in dBm
- `name`: The advertised device name

## Notes

- This integration requires the Home Assistant Bluetooth integration to be functional
- Devices must be actively advertising to be tracked
- The integration uses passive scanning, so it doesn't connect to devices
