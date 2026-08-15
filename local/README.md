# Local development

Run the project-local setup from the repository root:

```bash
./local/setup-local.sh
```

This creates `backend/.venv` and installs frontend dependencies. PostgreSQL is
provided only by Docker Compose. No private key files or SSH directories are
created or mounted; credentials are entered through the authenticated browser
and encrypted in PostgreSQL.

Start and verify:

```bash
cp .env.example .env
docker compose up -d --build
curl -fsS http://127.0.0.1:8080/health
```

Run checks:

```bash
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/pytest -q -o cache_dir=/tmp/nms-pytest-cache
(cd frontend && npm run build)
docker compose config --quiet
```

The automated SSH tests use generated keys and fake network adapters; they do
not require Cisco hardware.
