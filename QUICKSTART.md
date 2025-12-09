# Quick Start Guide

Get up and running with Home Assistant Bluetooth Tracker in minutes!

## Prerequisites

- Home Assistant OS or Supervised installation
- Bluetooth adapter (USB or built-in)
- Home Assistant Bluetooth integration enabled

## 5-Minute Setup

### Step 1: Install the Integration

**Option A: Manual Installation**
```bash
# Copy the integration to your Home Assistant
cd /config
mkdir -p custom_components
cp -r /path/to/custom_components/bluetooth_tracker custom_components/
```

**Option B: Via HACS**
1. Add this repository as a custom repository in HACS
2. Search for "Bluetooth Tracker"
3. Click Install

### Step 2: Restart Home Assistant

```bash
# In Home Assistant UI:
Settings → System → Restart
```

### Step 3: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Bluetooth Tracker"
4. Click on it to add
5. Click **Submit** (no configuration needed!)

✅ **Done!** Devices will start appearing automatically.

### Step 4: Install the Add-on (Optional)

1. Go to **Settings** → **Add-ons**
2. Click **Add-on Store**
3. Click the menu (⋮) → **Repositories**
4. Add: `https://github.com/DanielHabenicht/aitest.homeassistant-bluetooth-tracker`
5. Find "Bluetooth Advertisement Monitor"
6. Click **Install**
7. Configure the port (default: 8099)
8. Click **Start**

✅ **Access at:** `http://homeassistant.local:8099`

## First Steps

### View Your Devices

1. Go to **Settings** → **Devices & Services**
2. Click on **Bluetooth Tracker**
3. You'll see all discovered devices

### Create Your First Automation

```yaml
automation:
  - alias: "Device Detected"
    trigger:
      - platform: state
        entity_id: device_tracker.bluetooth_tracker_*
        to: "home"
    action:
      - service: notify.persistent_notification
        data:
          message: "Bluetooth device detected!"
```

### View Advertisement Data

1. Open web browser
2. Navigate to: `http://YOUR_HOME_ASSISTANT_IP:8099`
3. Watch Bluetooth advertisements in real-time
4. See HEX and ASCII data

## Troubleshooting

### No Devices Appearing?

1. Check Bluetooth is enabled:
   - Go to **Settings** → **System** → **Hardware**
   - Look for Bluetooth adapter

2. Check integration logs:
   ```yaml
   # configuration.yaml
   logger:
     default: info
     logs:
       custom_components.bluetooth_tracker: debug
   ```

3. Restart Home Assistant

### Add-on Not Starting?

1. Check add-on logs:
   - Go to **Settings** → **Add-ons**
   - Click "Bluetooth Advertisement Monitor"
   - Click **Log** tab

2. Ensure Bluetooth hardware is available:
   - Add-on needs access to Bluetooth adapter
   - Check system settings

3. Verify configuration:
   - Port must not be in use
   - Scan settings must be valid

## Next Steps

📖 Read the full documentation:
- [Main README](README.md)
- [Usage Examples](EXAMPLES.md)
- [Integration Documentation](custom_components/bluetooth_tracker/README.md)
- [Add-on Documentation](homeassistant_addon/README.md)

🚀 Try these examples:
- Set up presence detection
- Create room tracking automations
- Monitor beacon data
- Track signal strength

🤝 Get involved:
- [Contributing Guide](CONTRIBUTING.md)
- Report issues on GitHub
- Share your automations

## Common Questions

**Q: Will this track all Bluetooth devices?**
A: Yes, it tracks all devices that are actively advertising.

**Q: Does it need to pair with devices?**
A: No, it only listens to advertisements (passive scanning).

**Q: Can I filter specific devices?**
A: Currently no, but you can use Home Assistant filters in automations.

**Q: Will it drain battery?**
A: No, it only receives advertisements, doesn't actively connect.

**Q: Can I see raw advertisement data?**
A: Yes, use the add-on web interface to see all data.

## Need Help?

- 📘 Check [EXAMPLES.md](EXAMPLES.md) for usage scenarios
- 🐛 Report issues on GitHub
- 💡 Request features via GitHub Issues

---

**Ready to explore?** Start with the [Examples](EXAMPLES.md) to see what's possible!
