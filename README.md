# thingino-hub-cli

CLI client for Thingino Hub API v2.

## Quick start

```sh
cd /home/paul/thingino/hub-cli
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
