# Testing Guide

This guide explains how to test both the Home Assistant integration and add-on locally.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Make (optional, but recommended)

### Run All Tests

```bash
make test
```

Or manually:

```bash
# Test integration syntax
python3 -m py_compile custom_components/bluetooth_tracker/*.py

# Test add-on syntax
python3 -m py_compile homeassistant_addon/rootfs/app/*.py

# Run linting
flake8 custom_components/bluetooth_tracker
flake8 homeassistant_addon/rootfs/app
```

## Local Testing with Docker Compose

### Option 1: Full Environment (requires Bluetooth hardware)

Start Home Assistant and the add-on with real Bluetooth:

```bash
docker-compose up
```

This will start:
- Home Assistant on http://localhost:8123
- Bluetooth Monitor add-on on http://localhost:8099

### Option 2: Test Environment (no Bluetooth required)

Run automated tests:

```bash
make test-local
```

Or manually:

```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

This will:
1. Build and start Home Assistant
2. Build and start the add-on
3. Run automated tests
4. Exit with results

## Manual Testing

### Test the Integration

1. Start Home Assistant:
   ```bash
   docker-compose up homeassistant
   ```

2. Navigate to http://localhost:8123

3. Complete Home Assistant setup

4. Go to Settings → Devices & Services → Add Integration

5. Search for "Bluetooth Tracker"

6. Add the integration

7. Verify entities are created when Bluetooth devices are detected

### Test the Add-on

1. Start the add-on:
   ```bash
   docker-compose up bluetooth-monitor
   ```

2. Navigate to http://localhost:8099

3. Verify the web interface loads

4. Check that the API endpoint works:
   ```bash
   curl http://localhost:8099/api/advertisements
   ```

5. Verify HEX to ASCII conversion in the UI

## API Testing

### Test Add-on API

```bash
# Test web interface
curl http://localhost:8099/

# Test API endpoint
curl http://localhost:8099/api/advertisements

# Test with Python
python3 test-utils/test_addon.py
```

### Test Home Assistant API

```bash
# Check Home Assistant is running
curl http://localhost:8123/

# Run integration tests
python3 test-utils/test_integration.py
```

## Continuous Integration

The project includes GitHub Actions workflows:

### Integration CI (`.github/workflows/integration-ci.yml`)

Runs on push/PR and includes:
- Linting (flake8, pylint, black, isort)
- Manifest validation
- Syntax checking
- Import testing

### Add-on CI (`.github/workflows/addon-ci.yml`)

Runs on push/PR and includes:
- Linting (flake8, pylint, black, isort)
- Configuration validation
- Dockerfile linting
- Docker build (multi-arch)
- Container startup test

## Test Structure

```
.
├── .github/workflows/
│   ├── integration-ci.yml    # Integration CI pipeline
│   └── addon-ci.yml           # Add-on CI pipeline
├── test-config/               # Home Assistant test config
│   └── configuration.yaml
├── test-utils/                # Test utilities
│   ├── run_tests.py          # Main test runner
│   ├── test_integration.py   # Integration tests
│   └── test_addon.py         # Add-on tests
├── docker-compose.yml         # Full environment
├── docker-compose.test.yml    # Test environment
└── Makefile                   # Test commands
```

## Troubleshooting

### Home Assistant won't start

- Check logs: `docker-compose logs homeassistant`
- Verify configuration: `cat test-config/configuration.yaml`
- Check port 8123 is available: `netstat -an | grep 8123`

### Add-on won't start

- Check logs: `docker-compose logs bluetooth-monitor`
- Verify Dockerfile: `docker build homeassistant_addon/`
- Check port 8099 is available: `netstat -an | grep 8099`

### No Bluetooth devices detected

This is normal if:
- No Bluetooth hardware available
- No Bluetooth devices nearby
- Running in container without Bluetooth access

The tests handle this gracefully and will pass.

### Tests fail in CI

- Check GitHub Actions logs
- Verify all dependencies are installed
- Ensure code follows linting rules:
  ```bash
  black custom_components/bluetooth_tracker
  black homeassistant_addon/rootfs/app
  isort custom_components/bluetooth_tracker
  isort homeassistant_addon/rootfs/app
  ```

## Cleanup

```bash
# Stop all services
make down

# Clean up artifacts
make clean
```

Or manually:

```bash
docker-compose down -v
rm -rf test-config/.storage test-config/*.db
```

## Running Specific Tests

### Test Integration Only

```bash
make test-integration
```

### Test Add-on Only

```bash
make test-addon
```

### Test with Verbose Output

```bash
docker-compose -f docker-compose.test.yml up --build
```

## Development Workflow

1. Make changes to code
2. Run linting: `make lint`
3. Run tests: `make test`
4. Test locally: `make test-local`
5. Commit changes
6. CI will run automatically

## Performance Testing

To test with custom scan parameters:

```bash
docker-compose up -e SCAN_DURATION=5 -e SCAN_PAUSE=1
```

Or edit `docker-compose.yml` environment variables.

## Integration with Home Assistant

The integration is tested by:
1. Copying to Home Assistant's custom_components
2. Restarting Home Assistant
3. Adding via UI
4. Verifying functionality

See `docker-compose.yml` for the volume mount configuration.
