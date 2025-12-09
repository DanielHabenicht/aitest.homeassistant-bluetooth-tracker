#!/usr/bin/with-contenv bashio

# Get configuration
PORT=$(bashio::config 'port')

bashio::log.info "Starting Bluetooth Advertisement Monitor on port ${PORT}"

# Start the Python application
exec python3 /app/monitor.py --port "${PORT}"
