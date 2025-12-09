# Usage Examples

This document provides practical examples of using the Bluetooth Tracker integration and add-on.

## Integration Examples

### Example 1: Presence Detection Automation

Track when a family member arrives home based on their phone's Bluetooth:

```yaml
automation:
  - alias: "Welcome Home"
    trigger:
      - platform: state
        entity_id: device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
        to: "home"
    action:
      - service: notify.mobile_app
        data:
          message: "Welcome home!"
```

### Example 2: Room Presence Based on RSSI

Determine which room someone is in based on signal strength:

```yaml
automation:
  - alias: "Detect Room Presence"
    trigger:
      - platform: state
        entity_id: device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
    condition:
      - condition: template
        value_template: "{{ state_attr('device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff', 'rssi') | int > -60 }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
```

### Example 3: Track Multiple Devices

Create a group to track multiple family members:

```yaml
group:
  family_devices:
    name: "Family at Home"
    entities:
      - device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
      - device_tracker.bluetooth_tracker_11_22_33_44_55_66
      - device_tracker.bluetooth_tracker_77_88_99_aa_bb_cc
```

### Example 4: Low Battery Alert

Monitor BLE devices and alert when signal strength drops (potential low battery):

```yaml
automation:
  - alias: "Low Signal Alert"
    trigger:
      - platform: numeric_state
        entity_id: device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
        value_template: "{{ state_attr('device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff', 'rssi') }}"
        below: -90
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Device {{ state_attr('device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff', 'name') }} has low signal strength"
```

## Add-on Examples

### Example 1: Monitor Beacon Data

Use the web interface to monitor iBeacon or Eddystone beacon advertisements:

1. Navigate to `http://homeassistant.local:8099`
2. Look for devices with manufacturer data
3. Analyze the HEX data to extract beacon information:
   - iBeacon: Manufacturer ID 0x004C (Apple)
   - Eddystone: Service UUID 0xFEAA

### Example 2: Debug BLE Device Communication

When developing BLE integrations:

1. Open the add-on web interface
2. Place your BLE device near the Home Assistant
3. Observe the advertisement data in real-time
4. Use the HEX to ASCII conversion to decode string data
5. Copy the UUIDs and data formats for your integration

### Example 3: Monitor Environmental Sensors

Track environmental sensors that broadcast data:

1. View the service data in the web interface
2. Look for specific service UUIDs (e.g., `0000181A-0000-1000-8000-00805F9B34FB` for environmental sensing)
3. Monitor the HEX data for temperature, humidity, etc.
4. Use the ASCII conversion to identify patterns

### Example 4: Track Device Coverage

Use RSSI values to understand Bluetooth coverage:

1. Open the web interface
2. Walk around with a BLE device
3. Monitor how RSSI changes in different rooms
4. Identify dead zones or areas with weak signals
5. Optimize placement of Bluetooth adapters

## Configuration Examples

### Add-on Configuration for High-Traffic Areas

For areas with many Bluetooth devices:

```yaml
port: 8099
scan_duration: 5
scan_pause: 1
max_device_age: 180
```

### Add-on Configuration for Low-Power Mode

For battery-powered Home Assistant installations:

```yaml
port: 8099
scan_duration: 10
scan_pause: 5
max_device_age: 600
```

### Add-on Configuration for Development

For active BLE development work:

```yaml
port: 8099
scan_duration: 1
scan_pause: 0
max_device_age: 60
```

## Lovelace Card Examples

### Example 1: Simple Device Tracker Card

```yaml
type: entity
entity: device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
```

### Example 2: Advanced Card with Attributes

```yaml
type: entities
entities:
  - entity: device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
    type: custom:multiple-entity-row
    name: My Phone
    show_state: false
    entities:
      - attribute: rssi
        name: Signal
        unit: dBm
      - attribute: address
        name: MAC
```

### Example 3: Map Card

```yaml
type: map
entities:
  - device_tracker.bluetooth_tracker_aa_bb_cc_dd_ee_ff
  - device_tracker.bluetooth_tracker_11_22_33_44_55_66
```

### Example 4: iFrame for Add-on

Embed the add-on web interface in Home Assistant:

```yaml
type: iframe
url: http://homeassistant.local:8099
aspect_ratio: 100%
```

## Tips and Best Practices

1. **RSSI Interpretation**:
   - -30 to -60 dBm: Excellent signal
   - -60 to -80 dBm: Good signal
   - -80 to -90 dBm: Weak signal
   - Below -90 dBm: Very weak signal

2. **Device Naming**:
   - Devices will use their advertised name if available
   - Otherwise, they'll be named "Bluetooth Device [MAC]"

3. **Performance**:
   - Adjust scan_duration and scan_pause based on your needs
   - Longer scan durations = more devices detected
   - Longer pauses = less CPU usage

4. **Privacy**:
   - MAC addresses of all nearby Bluetooth devices will be visible
   - Consider this when sharing screenshots or logs

5. **Troubleshooting**:
   - If devices aren't detected, check Bluetooth hardware
   - Ensure Home Assistant has Bluetooth access
   - Check add-on logs for scanning errors
