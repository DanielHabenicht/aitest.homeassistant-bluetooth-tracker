#!/usr/bin/env python3
"""Bluetooth Advertisement Monitor - Web Interface."""
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from bleak import BleakScanner
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store recent advertisements
advertisements: Dict[str, dict] = {}


def hex_to_ascii(hex_data: str) -> str:
    """Convert hex string to ASCII, replacing non-printable characters."""
    try:
        bytes_data = bytes.fromhex(hex_data)
        ascii_str = ""
        for byte in bytes_data:
            if 32 <= byte <= 126:  # Printable ASCII range
                ascii_str += chr(byte)
            else:
                ascii_str += f"\\x{byte:02x}"
        return ascii_str
    except Exception as e:
        logger.error(f"Error converting hex to ASCII: {e}")
        return "N/A"


async def scan_bluetooth():
    """Continuously scan for Bluetooth advertisements."""
    logger.info("Starting Bluetooth scanner...")
    
    def detection_callback(device, advertisement_data):
        """Handle detected Bluetooth advertisements."""
        address = device.address
        
        # Extract manufacturer data
        manufacturer_data = {}
        if advertisement_data.manufacturer_data:
            for company_id, data in advertisement_data.manufacturer_data.items():
                hex_data = data.hex()
                manufacturer_data[company_id] = {
                    "hex": hex_data,
                    "ascii": hex_to_ascii(hex_data),
                    "bytes": list(data),
                }
        
        # Extract service data
        service_data = {}
        if advertisement_data.service_data:
            for uuid, data in advertisement_data.service_data.items():
                hex_data = data.hex()
                service_data[str(uuid)] = {
                    "hex": hex_data,
                    "ascii": hex_to_ascii(hex_data),
                    "bytes": list(data),
                }
        
        # Store advertisement information
        advertisements[address] = {
            "name": device.name or "Unknown",
            "address": address,
            "rssi": advertisement_data.rssi,
            "local_name": advertisement_data.local_name,
            "manufacturer_data": manufacturer_data,
            "service_data": service_data,
            "service_uuids": advertisement_data.service_uuids or [],
            "last_seen": datetime.now().isoformat(),
        }
    
    scanner = BleakScanner(detection_callback=detection_callback)
    
    while True:
        try:
            await scanner.start()
            await asyncio.sleep(10)  # Scan for 10 seconds
            await scanner.stop()
            await asyncio.sleep(1)  # Brief pause before next scan
        except Exception as e:
            logger.error(f"Error during Bluetooth scanning: {e}")
            await asyncio.sleep(5)


# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bluetooth Advertisement Monitor</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .device {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .device-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .device-name {
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
        }
        .device-address {
            font-family: monospace;
            color: #666;
        }
        .rssi {
            background-color: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }
        .data-section {
            margin-top: 10px;
        }
        .data-label {
            font-weight: bold;
            color: #555;
            margin-top: 8px;
        }
        .data-content {
            background-color: #f9f9f9;
            padding: 8px;
            border-left: 3px solid #2196F3;
            margin-top: 5px;
            font-family: monospace;
            font-size: 12px;
            word-break: break-all;
        }
        .hex-data {
            color: #1976D2;
        }
        .ascii-data {
            color: #388E3C;
            margin-top: 5px;
        }
        .last-seen {
            color: #999;
            font-size: 12px;
            margin-top: 5px;
        }
        .no-devices {
            text-align: center;
            color: #999;
            padding: 40px;
            background-color: white;
            border-radius: 5px;
        }
        .refresh-info {
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }
    </style>
    <script>
        function refreshData() {
            fetch('/api/advertisements')
                .then(response => response.json())
                .then(data => {
                    displayDevices(data);
                })
                .catch(error => console.error('Error fetching data:', error));
        }
        
        function displayDevices(devices) {
            const container = document.getElementById('devices-container');
            
            if (Object.keys(devices).length === 0) {
                container.innerHTML = '<div class="no-devices">No Bluetooth devices detected yet. Please wait...</div>';
                return;
            }
            
            let html = '';
            for (const [address, device] of Object.entries(devices)) {
                html += `
                    <div class="device">
                        <div class="device-header">
                            <div>
                                <div class="device-name">${device.name}</div>
                                <div class="device-address">${device.address}</div>
                            </div>
                            <div class="rssi">${device.rssi} dBm</div>
                        </div>
                        
                        ${device.local_name ? `<div class="data-section"><div class="data-label">Local Name:</div><div class="data-content">${device.local_name}</div></div>` : ''}
                        
                        ${Object.keys(device.manufacturer_data).length > 0 ? `
                            <div class="data-section">
                                <div class="data-label">Manufacturer Data:</div>
                                ${Object.entries(device.manufacturer_data).map(([id, data]) => `
                                    <div class="data-content">
                                        <div><strong>Company ID:</strong> ${id}</div>
                                        <div class="hex-data"><strong>HEX:</strong> ${data.hex}</div>
                                        <div class="ascii-data"><strong>ASCII:</strong> ${data.ascii}</div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        
                        ${Object.keys(device.service_data).length > 0 ? `
                            <div class="data-section">
                                <div class="data-label">Service Data:</div>
                                ${Object.entries(device.service_data).map(([uuid, data]) => `
                                    <div class="data-content">
                                        <div><strong>UUID:</strong> ${uuid}</div>
                                        <div class="hex-data"><strong>HEX:</strong> ${data.hex}</div>
                                        <div class="ascii-data"><strong>ASCII:</strong> ${data.ascii}</div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        
                        ${device.service_uuids.length > 0 ? `
                            <div class="data-section">
                                <div class="data-label">Service UUIDs:</div>
                                <div class="data-content">${device.service_uuids.join(', ')}</div>
                            </div>
                        ` : ''}
                        
                        <div class="last-seen">Last seen: ${device.last_seen}</div>
                    </div>
                `;
            }
            container.innerHTML = html;
        }
        
        // Refresh data every 2 seconds
        setInterval(refreshData, 2000);
        
        // Initial load
        window.onload = refreshData;
    </script>
</head>
<body>
    <h1>Bluetooth Advertisement Monitor</h1>
    <div class="refresh-info">Auto-refreshing every 2 seconds</div>
    <div id="devices-container">
        <div class="no-devices">Loading...</div>
    </div>
</body>
</html>
"""


def create_app(port: int):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    @app.route("/")
    def index():
        """Serve the main page."""
        return render_template_string(HTML_TEMPLATE)
    
    @app.route("/api/advertisements")
    def get_advertisements():
        """Return current advertisements as JSON."""
        return jsonify(advertisements)
    
    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bluetooth Advertisement Monitor")
    parser.add_argument("--port", type=int, default=8099, help="Web server port")
    args = parser.parse_args()
    
    # Create Flask app
    app = create_app(args.port)
    
    # Start Bluetooth scanning in background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    import threading
    scan_thread = threading.Thread(
        target=lambda: loop.run_until_complete(scan_bluetooth()),
        daemon=True
    )
    scan_thread.start()
    
    # Start web server
    logger.info(f"Starting web server on port {args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False)


if __name__ == "__main__":
    main()
