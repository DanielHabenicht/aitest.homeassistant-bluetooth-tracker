# CI/CD and Testing Overview

This document provides a comprehensive overview of the CI/CD and testing infrastructure added to the Home Assistant Bluetooth Tracker project.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐              ┌────────────────┐         │
│  │  Integration   │              │    Add-on      │         │
│  │  (custom_      │              │  (homeassistant│         │
│  │   components)  │              │      _addon)   │         │
│  └────────┬───────┘              └────────┬───────┘         │
│           │                               │                  │
│           ▼                               ▼                  │
│  ┌─────────────────────────────────────────────────┐        │
│  │         GitHub Actions Workflows                 │        │
│  │  ┌─────────────────┐  ┌──────────────────┐     │        │
│  │  │ Integration CI  │  │    Add-on CI      │     │        │
│  │  │  • Lint         │  │    • Lint         │     │        │
│  │  │  • Validate     │  │    • Validate     │     │        │
│  │  │  • Test         │  │    • Build        │     │        │
│  │  └─────────────────┘  └──────────────────┘     │        │
│  └─────────────────────────────────────────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Local Development Environment                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────┐         ┌──────────────────┐         │
│  │  Docker Compose   │         │   Test Utilities │         │
│  │  ┌─────────────┐  │         │  ┌────────────┐  │         │
│  │  │ Home        │  │         │  │ run_tests  │  │         │
│  │  │ Assistant   │  │         │  │   .py      │  │         │
│  │  │   :8123     │  │         │  ├────────────┤  │         │
│  │  └─────────────┘  │         │  │ test_      │  │         │
│  │  ┌─────────────┐  │         │  │ integration│  │         │
│  │  │ Bluetooth   │  │         │  │   .py      │  │         │
│  │  │ Monitor     │  │         │  ├────────────┤  │         │
│  │  │   :8099     │  │         │  │ test_addon │  │         │
│  │  └─────────────┘  │         │  │   .py      │  │         │
│  └───────────────────┘         │  └────────────┘  │         │
│                                 └──────────────────┘         │
│                                                               │
│  ┌───────────────────────────────────────────────┐          │
│  │              Makefile Commands                 │          │
│  │  • make test        - Run all tests            │          │
│  │  • make test-local  - Docker Compose tests     │          │
│  │  • make up          - Start services           │          │
│  │  • make lint        - Lint code                │          │
│  └───────────────────────────────────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components Added

### 1. GitHub Actions Workflows

#### `.github/workflows/integration-ci.yml`
- **Purpose:** Validate Home Assistant integration code
- **Triggers:** Push to main/copilot branches, PRs, file changes
- **Steps:**
  - Install Python 3.11
  - Install linting tools (flake8, pylint, black, isort)
  - Run syntax checks
  - Validate manifest.json and strings.json
  - Install Home Assistant for validation

#### `.github/workflows/addon-ci.yml`
- **Purpose:** Validate and build Home Assistant add-on
- **Triggers:** Push to main/copilot branches, PRs, file changes
- **Steps:**
  - Install Python 3.11
  - Install linting tools
  - Validate config.yaml
  - Lint Dockerfile with hadolint
  - Build Docker image (multi-arch)
  - Test container startup

### 2. Docker Compose Configurations

#### `docker-compose.yml`
- **Purpose:** Full local development environment
- **Services:**
  - `homeassistant`: Home Assistant on port 8123
  - `bluetooth-monitor`: Add-on on port 8099
  - `bluetooth-simulator`: Optional BLE device simulator
- **Features:**
  - Host network mode for Bluetooth access
  - Volume mounts for custom components
  - Environment variable configuration

#### `docker-compose.test.yml`
- **Purpose:** Automated testing environment
- **Services:**
  - `homeassistant-test`: HA with health checks
  - `addon-test`: Add-on with health checks
  - `test-runner`: Automated test execution
- **Features:**
  - Health checks for service readiness
  - Automated test execution
  - Clean exit after tests complete

### 3. Test Utilities

#### `test-utils/run_tests.py`
- Comprehensive test runner for Docker Compose environment
- Tests both integration and add-on
- Validates API endpoints and data structures
- Checks HEX to ASCII conversion
- Provides detailed test results

#### `test-utils/test_integration.py`
- Integration-specific tests
- Manifest validation
- Strings validation
- Home Assistant API testing

#### `test-utils/test_addon.py`
- Add-on-specific tests
- Web interface testing
- API endpoint validation
- Data structure verification
- HEX/ASCII conversion testing

### 4. Build System

#### `Makefile`
Convenient commands for common tasks:
- `make test` - Run all tests
- `make test-integration` - Test integration only
- `make test-addon` - Test add-on only
- `make test-local` - Run Docker Compose tests
- `make lint` - Lint all code
- `make build` - Build Docker image
- `make up` - Start services
- `make down` - Stop services
- `make logs` - View logs
- `make clean` - Clean up artifacts

### 5. Configuration

#### `test-config/configuration.yaml`
- Basic Home Assistant configuration
- Enables required integrations (API, frontend, Bluetooth)
- Debug logging for custom component
- Test-friendly settings

#### `test-config/.gitignore`
- Ignores runtime files (databases, logs)
- Keeps repository clean

### 6. Documentation

#### `TESTING.md`
- Complete testing guide
- Quick start instructions
- Docker Compose usage
- Manual testing procedures
- API testing examples
- Troubleshooting tips

#### `TEST_RESULTS.md`
- Summary of tests performed
- Test execution results
- Coverage information
- Known limitations
- Future enhancements

#### `.github/workflows/README.md`
- CI/CD workflow documentation
- Trigger conditions
- Job descriptions
- Local testing instructions

#### `CI_CD_OVERVIEW.md` (this file)
- High-level architecture
- Component descriptions
- Testing workflows
- Best practices

## Testing Workflows

### Development Workflow

```bash
# 1. Make code changes
vim custom_components/bluetooth_tracker/device_tracker.py

# 2. Lint code
make lint

# 3. Run tests
make test

# 4. Test locally with Docker
make test-local

# 5. Commit changes
git add .
git commit -m "Update device tracker"
git push

# 6. CI automatically runs on push
```

### CI/CD Workflow

```
Push to GitHub
    ├─→ Integration CI
    │   ├─→ Lint (flake8, pylint, black, isort)
    │   ├─→ Validate (manifest, strings)
    │   └─→ Test (syntax, imports)
    │
    └─→ Add-on CI
        ├─→ Lint (flake8, pylint, black, isort)
        ├─→ Validate (config.yaml, Dockerfile)
        ├─→ Build (Docker multi-arch)
        └─→ Test (container startup)

All checks pass → PR can be merged
```

### Local Testing Workflow

```
make test-local
    ├─→ Build Docker images
    ├─→ Start services
    │   ├─→ Home Assistant (health check)
    │   └─→ Bluetooth Monitor (health check)
    ├─→ Run test-runner
    │   ├─→ Test add-on web interface
    │   ├─→ Test add-on API
    │   ├─→ Test Home Assistant API
    │   └─→ Verify HEX/ASCII conversion
    └─→ Display results
```

## Test Coverage

### Integration
| Component | Syntax | Config | Structure | Runtime |
|-----------|--------|--------|-----------|---------|
| __init__.py | ✅ | ✅ | ✅ | ⚠️ |
| config_flow.py | ✅ | ✅ | ✅ | ⚠️ |
| device_tracker.py | ✅ | ✅ | ✅ | ⚠️ |
| manifest.json | ✅ | ✅ | ✅ | ✅ |
| strings.json | ✅ | ✅ | ✅ | ✅ |

### Add-on
| Component | Syntax | Config | Structure | Runtime |
|-----------|--------|--------|-----------|---------|
| monitor.py | ✅ | ✅ | ✅ | ⚠️ |
| config.yaml | ✅ | ✅ | ✅ | ✅ |
| Dockerfile | ✅ | ✅ | ✅ | ⚠️ |

✅ = Fully tested | ⚠️ = Requires specific environment

## Best Practices

### Before Committing
```bash
# Format code
black custom_components/bluetooth_tracker
black homeassistant_addon/rootfs/app

# Sort imports
isort custom_components/bluetooth_tracker
isort homeassistant_addon/rootfs/app

# Run tests
make test
```

### During Development
```bash
# Start services
make up

# View logs
make logs

# Make changes and test
# ... edit code ...
make test

# Stop services
make down
```

### For Pull Requests
1. Ensure all CI checks pass
2. Run local tests with `make test-local`
3. Document any new features
4. Update tests if needed

## Continuous Integration Features

### Automatic Checks
- ✅ Code formatting (black)
- ✅ Import sorting (isort)
- ✅ Syntax errors (flake8)
- ✅ Code complexity (flake8)
- ✅ Code analysis (pylint)
- ✅ Configuration validation
- ✅ Docker build validation

### Multi-Branch Support
- Runs on `main` branch
- Runs on `copilot/**` branches
- Runs on pull requests

### Failure Handling
- Clear error messages
- Suggests fixes
- Links to documentation

## Future Enhancements

### Planned
1. **Unit Tests**
   - Add pytest tests with mocks
   - Test individual functions
   - Increase code coverage

2. **Integration Tests**
   - Use Home Assistant test framework
   - Test entity lifecycle
   - Test state updates

3. **Performance Tests**
   - Load testing
   - Memory usage monitoring
   - Scan performance metrics

4. **Security Tests**
   - Dependency scanning
   - Container vulnerability scanning
   - Secret scanning

### Ideas
- Automated release process
- Documentation generation
- Code coverage reporting
- Performance benchmarking
- Multi-platform testing

## Resources

- **Main README:** [README.md](README.md)
- **Testing Guide:** [TESTING.md](TESTING.md)
- **Test Results:** [TEST_RESULTS.md](TEST_RESULTS.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)
- **Examples:** [EXAMPLES.md](EXAMPLES.md)

## Support

For issues with CI/CD or testing:
1. Check workflow logs in GitHub Actions
2. Review [TESTING.md](TESTING.md)
3. Run tests locally with `make test-local`
4. Open an issue on GitHub

---

**Last Updated:** 2025-12-09
**CI/CD Status:** ✅ Operational
