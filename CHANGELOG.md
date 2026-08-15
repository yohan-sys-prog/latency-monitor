# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-08-15

### Added
- Multi-target ping monitoring with configurable intervals
- Real-time latency tracking (current, min, max, average)
- Packet loss percentage calculation and tracking
- SQLite-based persistent storage for measurements and incidents
- Live Flask web dashboard with real-time refresh
- Chart.js powered latency graphs with historical visualization
- Automatic recovery detection after service outages
- Incident tracking and history
- Multi-channel alert notifications:
  - Email via SMTP with TLS support
  - Discord webhook integration with embeds
  - Slack webhook integration with formatted blocks
  - Generic JSON webhook support
- User account management with JWT authentication
- Role-based access control (admin/user roles)
- Password hashing with PBKDF2 and salt
- Production-grade REST API:
  - Versioned endpoints (/api/v1/)
  - Standard JSON response format
  - Per-endpoint rate limiting
  - CORS header support
  - Comprehensive error handling (404, 401, 403, 500)
- Docker containerization:
  - Multi-stage Dockerfile with security best practices
  - Non-root user execution
  - Health checks via HTTP endpoint
  - Docker Compose with production settings
  - Resource limits and logging configuration
- GitHub Actions CI/CD pipeline:
  - Automated testing on multiple Python versions
  - Code quality checks (flake8, pylint)
  - Security scanning (Bandit, Safety, Trivy)
  - Docker image building and validation
  - Automated release management
- Comprehensive documentation:
  - README with quick-start guide
  - Deployment guide for multiple platforms
  - Contributing guidelines
  - API documentation
- CLI monitoring mode for terminal-based monitoring
- Configuration management via JSON files
- Alert cooldown to prevent alert spam

### Architecture
- Layered modular design for maintainability
- Separation of concerns (monitor, storage, alerts, notifications, auth, api)
- Extensible notification system
- Abstract storage layer for future database support

### Testing
- Comprehensive unit test suite (6 tests)
- Test coverage for:
  - Multi-target monitoring
  - SQLite persistence
  - Alert evaluation and cooldown
  - Packet loss calculation
  - Recovery detection
  - Configuration loading

### Security Features
- JWT token-based authentication
- Password hashing with PBKDF2
- Role-based access control
- Non-root Docker execution
- HTTPS-ready (reverse proxy compatible)
- Input validation on API endpoints
- Rate limiting per endpoint

## Development Roadmap

### Future Versions
- V1.1.0: Advanced metrics (jitter, packet loss trends)
- V1.2.0: Dashboard customization and saved views
- V2.0.0: Multi-database support (PostgreSQL, MySQL)
- V2.1.0: Distributed monitoring with agent architecture
- V3.0.0: Integration with monitoring platforms (Prometheus, Grafana)

## Notes

This is the initial v1.0.0 release of latency-monitor, featuring a complete monitoring solution suitable for both small deployments and scaling toward enterprise use.

The project is actively maintained and welcomes contributions. See CONTRIBUTING.md for guidelines.
