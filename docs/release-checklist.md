# Release checklist

- [ ] No credentials, private keys, passwords, populated environment files, or
  real device data are tracked.
- [ ] Backend tests and frontend build pass.
- [ ] `docker compose config --quiet` passes and only web publishes a host port.
- [ ] The API has no host SSH mount or agent integration.
- [ ] First-run setup, login/logout, password change, and restart-lock behavior
  are verified.
- [ ] Credential responses contain metadata only and referenced credentials
  cannot be deleted.
- [ ] Unknown host keys require trust and changed host keys block connection.
- [ ] Modern and Cisco Legacy behavior is scoped per device.
- [ ] Device status is described as the latest explicit SSH operation, not
  continuous monitoring.
- [ ] Logs contain only sanitized connection categories.
