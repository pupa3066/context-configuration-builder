# Installing on another system (for testing)

Zero dependencies for the core (POSIX `sh`). Safe: non-destructive, no network. See SECURITY.md.

## Option A - agent-neutral core (recommended)
```sh
git clone https://github.com/pupa3066/context-configuration-builder.git
cd context-configuration-builder
sh install-core.sh                 # scaffolds ~/.context-config-builder (skips existing files)
sh adapters/kiro.sh apply          # or claude-code.sh / cursor.sh / generic.sh
```

## Option B - Kiro-native
```sh
sh install.sh                      # installs into ~/.kiro directly
```

## Option C - Kiro self-activating (override + resources + hooks + integrity check)
`install.sh` and the adapters copy content only. To make Kiro load CCB and self-verify
automatically on every new session, run the bootstrap. It is idempotent and self-checking:
```sh
sh ccb-bootstrap.sh                # wires ~/.kiro and verifies in one shot
```
What it does (all under `$KIRO_HOME`, default `~/.kiro`):
1. installs the hook scripts into `~/.kiro/hooks` (executable)
2. copies always-on steering into `~/.kiro/steering` (non-destructive: never clobbers edited files)
3. sets `chat.disableInheritingDefaultResources=true` in `settings/cli.json` (CCB becomes source of truth)
4. declares the CCB `resources[]` and registers the `agentSpawn` hooks in `agents/default.json`
   (integrity check ordered first; a timestamped `.bak.<ts>` is written before any edit)
5. runs `ccb-integrity-check.sh` and prints a PASS/FAIL report

Re-running is safe: existing steering is skipped, config is edited only if the desired state is
missing, and no backup is created when nothing changes. Preview first with `--dry-run`.

After install, every new Kiro session runs the integrity check automatically. Re-check manually:
```sh
sh ~/.kiro/hooks/ccb-integrity-check.sh
```

## Verify it works without touching your real setup
```sh
sh demo/demo.sh                    # clean-room walkthrough in a temp dir; changes nothing
```

## Custom locations (isolate a test)
```sh
CCB_HOME=/tmp/ccb-test sh install-core.sh
CCB_HOME=/tmp/ccb-test KIRO_HOME=/tmp/kiro-test sh adapters/kiro.sh apply
```

## Manage projects & rules
```sh
sh scripts/add-project.sh my-project
sh scripts/rules-builder.sh add "Confirm before bulk deletes" --section Repository
sh scripts/rules-builder.sh list
```

## Uninstall
Delete `~/.context-config-builder` (and any adapter output like `~/.kiro/steering/*` you added).
