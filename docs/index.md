# Health Checker

A Domain-Driven Design application that monitors HTTP endpoints, measures performance (TTFB), and tracks SSL certificate expiration. Results are accessible via a Telegram bot.

## Features

- HTTP status code monitoring
- Time to First Byte (TTFB) measurement
- SSL certificate expiration tracking
- Configurable alert thresholds for expiring certificates
- Full Telegram bot integration for URL management and result queries
- Complete historical record of all health checks
- Runs every 60 seconds via internal scheduler

## Documentation

- [Architecture Overview](architecture.md)
- [Domain Model](ddd-model.md)
- [Setup Guide](setup.md)
- [Configuration](configuration.md)
- [Telegram Commands](telegram-commands.md)
- [Changelog](changelog/)
