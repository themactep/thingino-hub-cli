# Changelog

## 0.1.0

- Initial standalone `thingino-hub-cli` scaffold
- Added commands:
  - `health`
  - `cameras list`
  - `cameras attention`
  - `actions refresh-api|refresh-onvif|refresh-snapshot|rescan|privacy|daynight|record`
  - `lifecycle enroll|connect|pair|delete`
  - `bulk run`
- Added unit tests for command groups and guardrails
- Added GitHub Actions CI workflow for multi-Python testing and packaging build
