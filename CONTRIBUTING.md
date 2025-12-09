# Contributing to Home Assistant Bluetooth Tracker

Thank you for your interest in contributing to this project!

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in the GitHub Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your Home Assistant version
   - Your setup (OS, Bluetooth hardware, etc.)

### Contributing Code

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes following the coding style
4. Test your changes thoroughly
5. Submit a pull request with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots (if applicable)

### Coding Standards

#### Python Code

- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

#### Home Assistant Integration

- Follow Home Assistant's integration quality scale
- Use async/await patterns where appropriate
- Include proper error handling
- Add logging with appropriate levels

#### Documentation

- Update README.md for significant changes
- Add examples for new features
- Keep documentation clear and concise
- Include screenshots for UI changes

## Development Setup

### Integration Development

1. Clone the repository
2. Copy `custom_components/bluetooth_tracker` to your Home Assistant's `custom_components` directory
3. Restart Home Assistant
4. Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.bluetooth_tracker: debug
```

### Add-on Development

1. Clone the repository
2. Set up a local add-on repository in Home Assistant
3. Install and test the add-on locally
4. Check add-on logs for issues

## Testing

### Manual Testing

- Test with various Bluetooth devices
- Verify entity creation and updates
- Check web interface functionality
- Test configuration changes
- Verify cleanup mechanisms

### Integration Testing

- Test integration setup through UI
- Test with different Bluetooth adapters
- Verify proper cleanup on unload
- Test with many devices

## Questions?

Feel free to open an issue for any questions about contributing!
