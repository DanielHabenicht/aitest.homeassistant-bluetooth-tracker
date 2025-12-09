# CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and testing.

## Workflows

### Integration CI (`integration-ci.yml`)

Validates the Home Assistant custom integration.

**Triggers:**
- Push to `main` branch
- Push to `copilot/**` branches
- Pull requests to `main`
- Changes to `custom_components/**` or workflow file

**Jobs:**

1. **Lint** - Code quality checks
   - flake8 (syntax errors and complexity)
   - pylint (code analysis)
   - black (code formatting)
   - isort (import sorting)

2. **Validate** - Configuration validation
   - Home Assistant installation
   - manifest.json validation
   - strings.json validation

3. **Test** - Code testing
   - pytest (if tests exist)
   - Syntax checking (py_compile)

### Add-on CI (`addon-ci.yml`)

Validates the Home Assistant add-on.

**Triggers:**
- Push to `main` branch
- Push to `copilot/**` branches
- Pull requests to `main`
- Changes to `homeassistant_addon/**` or workflow file

**Jobs:**

1. **Lint** - Code quality checks
   - flake8 (syntax errors and complexity)
   - pylint (code analysis)
   - black (code formatting)
   - isort (import sorting)

2. **Validate** - Configuration validation
   - config.yaml validation
   - Dockerfile linting (hadolint)

3. **Build** - Docker build test
   - Multi-architecture build (amd64)
   - Container startup test
   - Basic functionality check

4. **Test** - Code testing
   - Syntax checking (py_compile)
   - Import testing

## Workflow Status

View workflow runs at:
https://github.com/DanielHabenicht/aitest.homeassistant-bluetooth-tracker/actions

## Local Testing

Before pushing, run tests locally:

```bash
# Run all tests
make test

# Lint only
make lint

# Test with Docker
make test-local
```

## Adding New Tests

### Integration Tests

Add tests to `tests/` directory and pytest will pick them up automatically.

### Add-on Tests

Add tests to `test-utils/` and update the test runner scripts.

## Troubleshooting

### Linting Failures

Fix formatting issues:
```bash
black custom_components/bluetooth_tracker
black homeassistant_addon/rootfs/app
isort custom_components/bluetooth_tracker
isort homeassistant_addon/rootfs/app
```

### Validation Failures

- Check JSON/YAML syntax
- Verify all required fields present
- Ensure dependencies are correct

### Build Failures

- Check Dockerfile syntax
- Verify base image availability
- Test locally: `make build`

## Continuous Deployment

Currently workflows only perform validation. To add deployment:

1. Add repository secrets for deployment credentials
2. Add deployment jobs conditional on success
3. Tag releases for production deployments
