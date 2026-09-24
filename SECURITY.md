# Security

Consistent Context Kit is designed to be safe to install and run on any system.

## Network posture
- **The core tool makes NO network calls.** The installer, adapters, and scripts read
  and write only local files. No telemetry, no phone-home, no downloads.
- Verify yourself:
  ```sh
  grep -rnE "curl|wget|http|socket|urllib|requests|nc |ssh|scp" \
    install.sh install-core.sh scripts/ adapters/ core/ templates/ demo/
  # -> no matches
  ```
- The **optional `research/` pipeline** DOES make network calls (git clone of public
  repos, LLM API calls, dataset download)  -  but only when you explicitly run it, with
  your own keys. It is not part of the installable core and is opt-in.

## Filesystem posture
- Scripts write only under: `$CCB_HOME` (default `~/.context-config-builder`),
  `$KIRO_HOME` (default `~/.kiro`), or a target dir you pass explicitly.
- `install*.sh` are **non-destructive**: they never overwrite an existing file (skip-if-present).
- No `eval`, no dynamic code execution, no `sudo`. Pure POSIX `sh` with quoted paths.

## Secrets
- The tool neither reads nor stores secrets. Keep API keys (for the optional research
  pipeline) in your environment; they are never written to disk by this tool.

## Supply chain
- Zero runtime dependencies for the core (POSIX `sh` only).
- The research pipeline pins its Python deps in `research/harness/requirements.txt`.

## Reporting
Open a private security report to the maintainer before public disclosure.
