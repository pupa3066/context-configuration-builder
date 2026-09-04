# Contributing

Thanks for your interest in context-config-builder.

## License note
This project is under Business Source License 1.1. By contributing, you agree your
contributions are licensed under the same terms. Commercial redistribution/hosting
requires a license from the maintainer until the Change Date (see LICENSE).

## Ground rules
- Keep steering templates LEAN — they load into context every turn. Detail belongs in skills.
- No personal data in templates or examples. Keep them generic.
- POSIX `sh` for scripts (no bashisms). Test with `sh -n` and shellcheck if available.
- Label facts `[MEASURED]` vs `[CLAIM]` in any docs.

## Dev workflow
```sh
# lint scripts
for f in install.sh scripts/*.sh demo/*.sh; do sh -n "$f"; done
# clean-room test
sh demo/demo.sh
```

## Reporting issues
Include: OS + shell, Kiro CLI version, exact command, and expected vs actual behavior.
