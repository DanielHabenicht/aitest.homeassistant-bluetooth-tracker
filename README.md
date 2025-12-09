# Home Assistant Bluetooth Tracker

A comprehensive solution for Bluetooth device tracking in Home Assistant, consisting of two subprojects:

## Projects

### 1. Bluetooth Tracker Integration

A custom Home Assistant integration that automatically tracks Bluetooth devices through the official Bluetooth functionality.

**Features:**
- Automatic device discovery and entity creation
- Real-time tracking of all Bluetooth devices in range
- Device tracker entities with RSSI and device information
- Seamless integration with Home Assistant's device tracking

**Location:** `custom_components/bluetooth_tracker/`

[📖 Integration Documentation](custom_components/bluetooth_tracker/README.md)

### 2. Bluetooth Advertisement Monitor Add-on

A Home Assistant add-on that provides a web interface to view all Bluetooth advertisements with detailed data analysis.

**Features:**
- Real-time monitoring of all Bluetooth advertisements
- HEX to ASCII conversion for all data fields
- Detailed display of manufacturer data, service data, and UUIDs
- Auto-refreshing web interface

**Location:** `homeassistant_addon/`

[📖 Add-on Documentation](homeassistant_addon/README.md)

## Installation

### Integration Installation

#### Via HACS (Recommended)
1. Add this repository to HACS as a custom repository
2. Search for "Bluetooth Tracker" in HACS
3. Install the integration
4. Restart Home Assistant
5. Add the integration via Settings → Devices & Services

#### Manual Installation
1. Copy `custom_components/bluetooth_tracker` to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

### Add-on Installation

1. Add this repository to your Home Assistant Supervisor add-on store
2. Install the "Bluetooth Advertisement Monitor" add-on
3. Configure the port (default: 8099)
4. Start the add-on
5. Access the web interface at `http://homeassistant.local:8099`

## Usage

### Tracking Devices (Integration)

Once the integration is installed and configured:
1. All Bluetooth devices in range will be automatically discovered
2. Device tracker entities will be created automatically
3. Use these entities in automations, scripts, or lovelace cards

Example entity: `device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff`

### Monitoring Advertisements (Add-on)

Once the add-on is running:
1. Navigate to the web interface (default: port 8099)
2. View all Bluetooth advertisements in real-time
3. Inspect manufacturer data and service data in both HEX and ASCII
4. Monitor RSSI values for signal strength analysis

## Requirements

- Home Assistant with Bluetooth support
- Bluetooth hardware (USB adapter or built-in)
- Home Assistant OS or Supervised installation (for add-on)

## Use Cases

- **Device presence detection**: Track family members' phones, fitness trackers, or other Bluetooth devices
- **Smart home automation**: Trigger automations based on device presence
- **Bluetooth development**: Debug and analyze Bluetooth advertisements
- **Signal strength monitoring**: Track RSSI values for positioning or proximity detection

## Architecture

```
homeassistant-bluetooth-tracker/
├── custom_components/
│   └── bluetooth_tracker/          # Integration
│       ├── __init__.py
│       ├── config_flow.py
│       ├── device_tracker.py
│       ├── manifest.json
│       ├── strings.json
│       └── README.md
├── homeassistant_addon/            # Add-on
│   ├── config.yaml
│   ├── Dockerfile
│   ├── README.md
│   └── rootfs/
│       └── app/
│           ├── run.sh
│           └── monitor.py
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is provided as-is for use with Home Assistant.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.