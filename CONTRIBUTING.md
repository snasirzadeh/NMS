# Contributing

Thanks for contributing.

## Development Principles

- Keep network logic outside HTTP route handlers.
- Never commit private keys, credentials, or real customer/device data.
- Add tests for security-sensitive changes.
- Keep monitoring features out of scope until the project explicitly adds them.
- Update documentation when behavior changes.

## Pull Requests

Before opening a pull request:

1. Run backend tests.
2. Run frontend type checks/tests/build.
3. Confirm no secrets or private keys are present.
4. Explain architectural changes and trade-offs.
5. Keep the pull request focused.
