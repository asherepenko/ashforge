#!/usr/bin/env bash
# Codex plugins cannot declare agents, but Codex loads every *.toml under
# $CODEX_HOME/agents/ and follows symlinks there. Keep one link pointing at
# this plugin version's codex-agents/ so installs and updates need no manual step.
set -uo pipefail

want="${PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/codex-agents"
agents_dir="${CODEX_HOME:-$HOME/.codex}/agents"
link="$agents_dir/android-expert-toolkit"

[ -d "$want" ] || exit 0

if [ -L "$link" ]; then
  # Valid only when it targets this version and resolves; anything else is stale.
  [ "$(readlink "$link")" = "$want" ] && [ -d "$link" ] && exit 0
elif [ -e "$link" ]; then
  echo "android-expert-toolkit: $link exists and is not a symlink; leaving it alone" >&2
  exit 0
fi

mkdir -p "$agents_dir" && ln -sfn "$want" "$link" \
  || echo "android-expert-toolkit: could not link $link -> $want" >&2
exit 0
