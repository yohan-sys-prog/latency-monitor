# Contributing to latency-monitor

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the latency-monitor project.

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When creating a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots/logs if possible**
- **Include your environment details** (OS, Python version, Docker version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, provide the following information:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

- Fill in the required template
- Follow the Python code style guidelines
- Include appropriate test cases
- Document new code with docstrings
- End all files with a newline

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- pip

### Local Development

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/latency-monitor.git
   cd latency-monitor
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pylint flake8 coverage
   ```

5. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Making Changes

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use meaningful variable and function names
   - Add docstrings to all functions and classes
   - Maximum line length: 120 characters

2. **Testing**
   - Write tests for new features
   - Ensure all existing tests pass:
     ```bash
     python3 -m unittest discover -s tests -v
     ```
   - Aim for >80% code coverage:
     ```bash
     coverage run -m unittest discover -s tests
     coverage report -m
     ```

3. **Linting**
   - Run flake8:
     ```bash
     flake8 application/ tests/ --max-line-length=120
     ```
   - Run pylint:
     ```bash
     pylint application/ --disable=all --enable=E,F
     ```

### Commit Guidelines

- Use clear and descriptive commit messages
- Use the imperative mood ("Add feature" not "Added feature")
- Reference issues and pull requests liberally
- Limit the first line to 72 characters
- Provide more detailed explanation in the body if needed

Example:
```
Add latency threshold alerts

- Add latency_threshold_ms configuration parameter
- Implement AlertManager.evaluate() for threshold checking
- Add unit tests for alert evaluation logic

Fixes #123
```

### Submitting Changes

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub:
   - Use a clear, descriptive title
   - Reference related issues
   - Describe the changes in detail
   - Include testing information
   - Request review from maintainers

3. Address review feedback:
   - Make requested changes
   - Push updates to the same branch
   - Respond to all comments

## Project Structure

```
latency-monitor/
├── application/           # Main application package
│   ├── __init__.py
│   ├── monitor.py         # Ping monitor engine
│   ├── storage.py         # SQLite persistence
│   ├── config.py          # Configuration management
│   ├── alerts.py          # Alert evaluation
│   ├── notifications.py   # Email/webhook alerts
│   ├── history.py         # Historical data queries
│   ├── auth.py            # User authentication
│   ├── api.py             # API utilities
│   ├── dashboard.py       # Flask web application
│   └── cli.py             # CLI interface
├── templates/
│   └── dashboard.html     # Web interface
├── tests/
│   └── test_latency_monitor.py
├── .github/
│   └── workflows/         # GitHub Actions CI/CD
├── monitor_config.json    # Runtime configuration
├── notification_config.json  # Alert configuration
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
└── CONTRIBUTING.md
```

## Architecture Overview

The application follows a layered architecture:

1. **Monitor Layer** (monitor.py)
   - Executes ping commands
   - Tracks latency metrics
   - Calculates packet loss

2. **Storage Layer** (storage.py)
   - Manages SQLite database
   - Persists measurements and incidents

3. **Business Logic Layer** (alerts.py, history.py)
   - Evaluates alert conditions
   - Processes historical queries
   - Detects recovery events

4. **Notification Layer** (notifications.py)
   - Sends email alerts
   - Posts to webhooks
   - Manages notification delivery

5. **Authentication Layer** (auth.py)
   - Manages user accounts
   - Generates JWT tokens
   - Enforces access control

6. **API Layer** (api.py)
   - Provides standard response formats
   - Implements rate limiting
   - Validates input

7. **Presentation Layer** (dashboard.py, dashboard.html)
   - Flask web application
   - HTML dashboard interface
   - REST API endpoints

## Testing

### Running Tests

```bash
# Run all tests
python3 -m unittest discover -s tests -v

# Run specific test file
python3 -m unittest tests.test_latency_monitor -v

# Run specific test case
python3 -m unittest tests.test_latency_monitor.PingMonitorTests.test_multiple_targets_have_separate_stats
```

### Writing Tests

Tests should:
- Test one behavior per test method
- Use descriptive test names
- Include assertions with clear messages
- Clean up resources (databases, files, etc.)
- Mock external dependencies

Example:
```python
def test_alert_on_high_latency(self):
    """Alert should trigger when latency exceeds threshold"""
    metrics = {'current': 150, 'avg': 140, 'min': 100, 'max': 200, 'failed': 0}
    alert = self.alert_manager.evaluate(
        'example.com', metrics,
        latency_threshold_ms=100,
        packet_loss_threshold=10,
        cooldown_seconds=300
    )
    self.assertIsNotNone(alert)
    self.assertEqual(alert['reason'], 'High latency detected')
```

## Documentation

- Update README.md for user-facing changes
- Update DEPLOYMENT.md for deployment-related changes
- Add docstrings to all functions and classes
- Include examples in docstrings where appropriate
- Keep comments concise and meaningful

## Release Process

1. Update CHANGELOG.md with new features/fixes
2. Bump version in configuration
3. Create a git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions will automatically create a release
6. Add release notes on GitHub

## Questions or Need Help?

- Check the README.md and DEPLOYMENT.md
- Review existing issues and pull requests
- Create an issue with the "question" label
- Contact maintainers directly

## License

By contributing to this project, you agree that your contributions will be licensed under its MIT License.

Thank you for contributing to latency-monitor!
