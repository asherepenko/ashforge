#!/usr/bin/env bash
# Cursor loads user subagents from ~/.cursor/agents/*.md in the same Markdown
# format as agents/*.md, and nothing in a Claude plugin reaches that directory.
# Keep one symlink per agent pointing at this plugin version so installs and
# updates need no manual step. Runs only when Cursor's home exists.
set -uo pipefail

root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cursor_home="${CURSOR_HOME:-$HOME/.cursor}"
agents_dir="$cursor_home/agents"

[ -d "$root/agents" ] && [ -d "$cursor_home" ] || exit 0
mkdir -p "$agents_dir" || { echo "android-expert-toolkit: cannot create $agents_dir" >&2; exit 0; }

# Drop links from an earlier version whose agent no longer exists.
for link in "$agents_dir"/*.md; do
  [ -L "$link" ] || continue
  case "$(readlink "$link")" in
    */android-expert-toolkit/*/agents/*.md) [ -e "$link" ] || rm -f "$link" ;;
  esac
done

for want in "$root"/agents/*.md; do
  [ -f "$want" ] || continue
  link="$agents_dir/$(basename "$want")"
  if [ -L "$link" ]; then
    # Valid only when it targets this version and resolves; anything else is stale.
    [ "$(readlink "$link")" = "$want" ] && [ -f "$link" ] && continue
  elif [ -e "$link" ]; then
    echo "android-expert-toolkit: $link exists and is not a symlink; leaving it alone" >&2
    continue
  fi
  ln -sfn "$want" "$link" || echo "android-expert-toolkit: could not link $link -> $want" >&2
done
exit 0
