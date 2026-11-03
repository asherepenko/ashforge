#!/usr/bin/env bash
# Vendor pinned third-party skills into this plugin.
#
#   skills/community/<name>  from three MIT-licensed GitHub repos, at the commit
#                            pinned in ios-skills.lock (or --community-ref).
#   skills/xcode/<name>      from `xcrun agent skills export`, only with
#                            --update-xcode. Content depends on the installed
#                            Xcode build.
#
# Usage: scripts/sync-ios-skills.sh [--community-ref REF] [--update-xcode] [--fork-ref REF]
#
# Safety: every skill is staged and validated in a temp dir before anything in
# the tree changes. The lock is written last. Any failure exits 1 and leaves
# the tree and lock as they were. Never edit vendored files by hand.
set -euo pipefail

PLUGIN_ROOT="${IOS_SKILLS_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
COMMUNITY_DIR="$PLUGIN_ROOT/skills/community"
XCODE_DIR="$PLUGIN_ROOT/skills/xcode"
LOCK="$PLUGIN_ROOT/ios-skills.lock"

# name|repo|skill dir inside the repo|license
COMMUNITY=(
  "swift-concurrency|AvdLee/Swift-Concurrency-Agent-Skill|skills/swift-concurrency|MIT"
  "swift-testing-expert|AvdLee/Swift-Testing-Agent-Skill|swift-testing-expert|MIT"
  "swiftdata-pro|twostraws/SwiftData-Agent-Skill|swiftdata-pro|MIT"
)

XCODE_SKILLS=(
  swiftui-specialist
  swiftui-whats-new-27
  app-intents-specialist
  app-intents-whats-new-27
  xctrace
  modernize-tests
  audit-xcode-security-settings
  app-resizability
  device-interaction
)

die() { echo "sync-ios-skills: $*" >&2; exit 1; }

community_ref=""
update_xcode=0
fork_ref=""
while [ $# -gt 0 ]; do
  case "$1" in
    --community-ref) [ $# -ge 2 ] || { echo "sync-ios-skills: --community-ref needs a value" >&2; exit 2; }
                     community_ref="$2"; shift 2 ;;
    --fork-ref)      [ $# -ge 2 ] || { echo "sync-ios-skills: --fork-ref needs a value" >&2; exit 2; }
                     fork_ref="$2"; shift 2 ;;
    --update-xcode)  update_xcode=1; shift ;;
    *) echo "sync-ios-skills: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

lock_get() {
  [ -f "$LOCK" ] || return 0
  awk -F= -v k="$1" '$1==k { sub(/^[^=]*=/, ""); print; exit }' "$LOCK"
}

if [ -n "$fork_ref" ]; then
  if [ -f "$LOCK" ] && grep -q '^fork\.' "$LOCK"; then
    echo "sync-ios-skills: --fork-ref is not implemented yet" >&2
  else
    echo "sync-ios-skills: --fork-ref not implemented until fork exists" >&2
  fi
  exit 2
fi

work="$(mktemp -d)"
committed=0
swap_dests=()
swap_backups=()

# Undo swaps newest first. An entry is recorded before its first move, so each
# step checks what actually happened: with a backup present the old content is
# put back (dest holds the new content or nothing); without one the old content
# never moved and dest is left alone. No backup is expected for a dest that did
# not exist, so dest is removed there.
rollback() {
  local i d b
  [ "${#swap_dests[@]}" -gt 0 ] || return 0
  for ((i = ${#swap_dests[@]} - 1; i >= 0; i--)); do
    d="${swap_dests[$i]}"
    b="${swap_backups[$i]}"
    if [ -n "$b" ]; then
      if [ -e "$b" ] || [ -L "$b" ]; then
        rm -rf "$d"
        mv "$b" "$d"
      fi
    else
      rm -rf "$d"
    fi
  done
}
cleanup() {
  local rc=$?
  trap '' INT TERM
  if [ "$committed" -eq 0 ]; then rollback || true; fi
  rm -f "$LOCK.tmp.$$"
  rm -rf "$work"
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# Resolve a ref to one commit SHA: exact SHA, HEAD, branch or tag. A name that
# is both a branch and a tag pointing at different commits is rejected.
resolve_ref() {
  local repo="$1" ref="$2" out sha rf heads="" tag="" peeled=""
  if [[ "$ref" =~ ^[0-9a-f]{40}$ ]]; then echo "$ref"; return 0; fi
  if [ "$ref" = HEAD ]; then
    out="$(git ls-remote "https://github.com/$repo" HEAD)" || return 1
    sha="$(printf '%s\n' "$out" | head -1 | cut -f1)"
    [ -n "$sha" ] || return 1
    echo "$sha"; return 0
  fi
  out="$(git ls-remote "https://github.com/$repo" "refs/heads/$ref" "refs/tags/$ref" "refs/tags/$ref^{}")" || return 1
  [ -n "$out" ] || return 1
  while IFS=$'\t' read -r sha rf; do
    case "$rf" in
      "refs/heads/$ref")    heads="$sha" ;;
      "refs/tags/$ref^{}")  peeled="$sha" ;;
      "refs/tags/$ref")     tag="$sha" ;;
    esac
  done <<<"$out"
  tag="${peeled:-$tag}"
  if [ -n "$heads" ] && [ -n "$tag" ] && [ "$heads" != "$tag" ]; then
    echo "sync-ios-skills: ref '$ref' is ambiguous in $repo (branch and tag differ)" >&2
    return 1
  fi
  sha="${heads:-$tag}"
  [ -n "$sha" ] || return 1
  echo "$sha"
}

# Reject archive entries with `..` or an absolute path anywhere in the archive.
# Entries under the skill path, or a LICENSE file at the repo root, are the only
# ones extracted; those must be a regular file or directory (no symlinks,
# hardlinks, devices, fifos). Links elsewhere in the repo are never extracted,
# so they are ignored. The in-scope member list is written to the third argument.
check_tar() { # tgz skill-path members-file
  local tgz="$1" skill="$2" members="$3" line type rel cand in_scope
  tar -tzf "$tgz" >"$work/tar.names" 2>/dev/null || die "cannot read archive $tgz"
  tar -tvzf "$tgz" >"$work/tar.types" 2>/dev/null || die "cannot read archive $tgz"
  [ "$(wc -l <"$work/tar.names")" -eq "$(wc -l <"$work/tar.types")" ] || die "cannot read archive $tgz"
  : >"$members"
  while IFS= read -r line; do
    case "$line" in
      /*|..|../*|*/..|*/../*) die "unsafe path in archive: $line" ;;
    esac
  done <"$work/tar.names"
  while IFS= read -r line <&3 && IFS= read -r type <&4; do
    rel="${line#*/}"
    [ "$rel" != "$line" ] || continue
    in_scope=0
    case "$rel" in
      "$skill"|"$skill"/*) in_scope=1 ;;
    esac
    for cand in LICENSE LICENSE.md LICENSE.txt; do
      [ "$rel" = "$cand" ] && in_scope=1
    done
    [ "$in_scope" -eq 1 ] || continue
    case "${type:0:1}" in
      -|d) ;;
      *) die "unsafe entry (link or special file) in archive: $type" ;;
    esac
    printf '%s\n' "$line" >>"$members"
  done 3<"$work/tar.names" 4<"$work/tar.types"
}

# Value of `name:` in the SKILL.md frontmatter block.
fm_name() {
  awk '
    NR == 1 { if ($0 !~ /^---[[:space:]]*$/) exit; next }
    /^---[[:space:]]*$/ { exit }
    /^name:/ {
      sub(/^name:[[:space:]]*/, "")
      sub(/[[:space:]]+$/, "")
      gsub(/^["\x27]|["\x27]$/, "")
      print; exit
    }' "$1"
}

check_skill() { # dir expected-name
  [ -f "$1/SKILL.md" ] || die "$2: SKILL.md missing"
  local got
  got="$(fm_name "$1/SKILL.md")"
  [ "$got" = "$2" ] || die "$2: SKILL.md frontmatter name is '$got', expected '$2'"
}

mkdir -p "$work/stage/community" "$work/stage/xcode" "$work/backup"
swaps=()   # staged|dest

# --- Xcode build bookkeeping -------------------------------------------------
installed_build=""
installed_version=""
if command -v xcodebuild >/dev/null 2>&1; then
  xb="$(xcodebuild -version 2>/dev/null || true)"
  installed_version="$(printf '%s\n' "$xb" | sed -n 's/^Xcode //p' | head -1)"
  installed_build="$(printf '%s\n' "$xb" | sed -n 's/^Build version //p' | head -1)"
fi
if [ "$update_xcode" -eq 0 ]; then
  locked_build="$(lock_get xcode.build)"
  if [ -n "$locked_build" ] && [ -n "$installed_build" ] && [ "$locked_build" != "$installed_build" ]; then
    echo "sync-ios-skills: warning: installed Xcode build $installed_build differs from locked $locked_build; run with --update-xcode to refresh skills/xcode" >&2
  fi
fi

# --- Community skills --------------------------------------------------------
lock_community=()
for entry in "${COMMUNITY[@]}"; do
  IFS='|' read -r name repo path license <<<"$entry"
  ref="${community_ref:-$(lock_get "community.$name.commit")}"
  ref="${ref:-HEAD}"
  sha="$(resolve_ref "$repo" "$ref")" || die "cannot resolve ref '$ref' in $repo"
  tgz="$work/$name.tgz"
  curl -fsSL "https://codeload.github.com/$repo/tar.gz/$sha" -o "$tgz" || die "cannot download $repo@$sha"
  check_tar "$tgz" "$path" "$work/$name.members"
  src="$work/src-$name"
  mkdir "$src"
  tar -xzf "$tgz" -C "$src" --strip-components=1 -T "$work/$name.members" || die "cannot extract $repo@$sha"
  [ -d "$src/$path" ] || die "$name: '$path' not found in $repo@$sha"
  lic_file=""
  for cand in LICENSE LICENSE.md LICENSE.txt; do
    if [ -f "$src/$cand" ]; then lic_file="$src/$cand"; break; fi
  done
  [ -n "$lic_file" ] || die "$name: no LICENSE in $repo@$sha"
  cp -R "$src/$path" "$work/stage/community/$name"
  cp "$lic_file" "$work/stage/community/$name/LICENSE"
  check_skill "$work/stage/community/$name" "$name"
  swaps+=("$work/stage/community/$name|$COMMUNITY_DIR/$name")
  lock_community+=("community.$name.repo=$repo" "community.$name.commit=$sha" "community.$name.license=$license" "community.$name.path=$path")
done

# --- Xcode skills ------------------------------------------------------------
lock_xcode=()
if [ "$update_xcode" -eq 1 ]; then
  command -v xcrun >/dev/null 2>&1 || die "--update-xcode needs xcrun (install Xcode)"
  [ -n "$installed_build" ] || die "--update-xcode needs xcodebuild -version to report the build"
  mkdir "$work/xport"
  xcrun agent skills export --output-dir "$work/xport" >"$work/xport.log" 2>&1 \
    || die "xcrun agent skills export failed: $(tail -3 "$work/xport.log")"
  [ -z "$(find "$work/xport" -type l | head -1)" ] || die "Xcode export contains a symlink"
  for name in "${XCODE_SKILLS[@]}"; do
    [ -d "$work/xport/$name" ] || die "$name: missing from Xcode export"
    cp -R "$work/xport/$name" "$work/stage/xcode/$name"
    check_skill "$work/stage/xcode/$name" "$name"
    swaps+=("$work/stage/xcode/$name|$XCODE_DIR/$name")
  done
  lock_xcode+=("xcode.version=$installed_version" "xcode.build=$installed_build")
  for name in "${XCODE_SKILLS[@]}"; do lock_xcode+=("xcode.skill=$name"); done
elif [ -f "$LOCK" ]; then
  while IFS= read -r line; do lock_xcode+=("$line"); done < <(grep '^xcode\.' "$LOCK" || true)
fi

lock_fork=()
if [ -f "$LOCK" ]; then
  while IFS= read -r line; do lock_fork+=("$line"); done < <(grep '^fork\.' "$LOCK" || true)
fi

# --- Swap everything in, then write the lock last ----------------------------
# INT/TERM are ignored from the first move until the lock is in place, so the
# swap, the lock write and the commit flag cannot be split by a signal.
trap '' INT TERM
n=0
for pair in "${swaps[@]}"; do
  staged="${pair%%|*}"
  dest="${pair#*|}"
  if [ -d "$dest" ] && diff -r "$staged" "$dest" >/dev/null 2>&1; then continue; fi
  mkdir -p "$(dirname "$dest")"
  backup=""
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    n=$((n + 1))
    backup="$work/backup/$n"
  fi
  swap_dests+=("$dest")
  swap_backups+=("$backup")
  if [ -n "$backup" ]; then mv "$dest" "$backup"; fi
  mv "$staged" "$dest"
done

{
  echo "# Generated by scripts/sync-ios-skills.sh; do not edit."
  printf '%s\n' "${lock_community[@]}"
  if [ "${#lock_xcode[@]}" -gt 0 ]; then printf '%s\n' "${lock_xcode[@]}"; fi
  if [ "${#lock_fork[@]}" -gt 0 ]; then printf '%s\n' "${lock_fork[@]}"; fi
} >"$work/lock.new"

if [ ! -f "$LOCK" ] || ! cmp -s "$work/lock.new" "$LOCK"; then
  cp "$work/lock.new" "$LOCK.tmp.$$"
  mv "$LOCK.tmp.$$" "$LOCK"
fi
committed=1
trap 'exit 130' INT TERM

echo "Synced ${#COMMUNITY[@]} community skills$([ "$update_xcode" -eq 1 ] && echo " and ${#XCODE_SKILLS[@]} Xcode skills")"
