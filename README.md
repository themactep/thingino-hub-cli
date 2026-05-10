# thingino-hub-cli

CLI client for Thingino Hub API v2.

## Quick start

```sh
git clone https://github.com/themactep/thingino-hub-cli
cd thingino-hub-cli
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Set your hub API base URL (default is `http://127.0.0.1:8090`):

```sh
export THINGINO_HUB_BASE_URL="http://127.0.0.1:8090"
```

## Commands

```sh
hub-cli health
hub-cli cameras list
hub-cli cameras attention --minimum-severity high
hub-cli actions refresh-api cam1
hub-cli actions privacy cam1 --disabled
hub-cli lifecycle enroll --ip 192.168.88.155 --onvif-username thingino --onvif-password thingino
hub-cli lifecycle connect cam1
hub-cli lifecycle pair cam1
hub-cli bulk run --action refresh-api --camera-id cam1 --camera-id cam2
```

JSON output:

```sh
hub-cli --json cameras list
```

## Global options

- `--base-url` (env: `THINGINO_HUB_BASE_URL`)
- `--timeout` (env: `THINGINO_HUB_TIMEOUT`)
- `--insecure` (disable TLS verification)
- `--json` (machine-readable output)

## Safety and exit codes

- API/request failures return exit code `1`
- `lifecycle delete` requires `--yes`

## Development

```sh
pytest -q
```

## Releases

- CI runs on pushes/PRs across Python 3.11–3.13
- Tagging `v*` creates a GitHub release with built wheel/sdist artifacts
- Version history is tracked in [CHANGELOG.md](CHANGELOG.md)
