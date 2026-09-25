#!/bin/sh
# agent-parity-probe.sh - ask Model and Claude Code the SAME question about their session-start context
# and print both answers side by side. Each agent must answer from loaded context only (no tools), so the
# answer reflects what actually reached context, not what is on disk.
#
# Usage: sh scripts/agent-parity-probe.sh [launch-dir]      (default: $HOME)
# Needs: kiro-cli and claude on PATH, both signed in. Costs one short request per agent.
set -u
DIR="${1:-$HOME}"
Q="Answer ONLY from context loaded at session start; call no tools. Terse numbered list.
1) Quote the final [ccb-integrity] line, or NONE.
2) Quote the final [ccb-parity] line, or NONE.
3) Quote the [ccb-project-context] block verbatim, or NONE.
4) How many times does the literal header '=== PROJECT CONTEXT:' appear in your session-start context?
5) List the project skill names exactly as you would invoke them.
6) Was any session-start output truncated? yes/no."
strip() { sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -v '^[[:space:]]*$' | grep -v 'hooks finished\|WARNING: --trust-tools\|Credits:'; }
echo "launch dir: $DIR"
echo "=== Model ($(kiro-cli --version 2>/dev/null))"
( cd "$DIR" && kiro-cli chat --no-interactive --trust-tools= "$Q" 2>&1 | strip )
echo "=== Claude Code ($(claude --version 2>/dev/null))"
( cd "$DIR" && claude -p "$Q" < /dev/null 2>&1 )
