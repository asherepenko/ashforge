#!/usr/bin/env bash
# score-check.sh — flag a domain score that contradicts the member's own findings.
#
# The domain score is informational, but a 9 next to an open HIGH is a lazy
# score. These rules are first-match, top-down; the first match is the flag.
#
# Usage:
#   score-check.sh --score N [--critical N] [--high N] [--medium N] [--low N] [--weak N]
# --score is required (1-10). Other counts default to 0. LOW never flags.
# Output: "ok", or "FLAG: <reason naming the band>"
# Exit:   0 ok · 1 flag · 2 usage error

set -euo pipefail

usage() {
  echo "usage: score-check.sh --score 1-10 [--critical N] [--high N] [--medium N] [--low N] [--weak N]" >&2
  exit 2
}

int() { [[ "${1:-}" =~ ^[0-9]+$ ]] || usage; }

score="" critical=0 high=0 medium=0 weak=0
while [ $# -gt 0 ]; do
  case "$1" in
    --score)    int "${2:-}"; score=$2; shift 2 ;;
    --critical) int "${2:-}"; critical=$2; shift 2 ;;
    --high)     int "${2:-}"; high=$2; shift 2 ;;
    --medium)   int "${2:-}"; medium=$2; shift 2 ;;
    # LOW never moves the check; accepted so callers can pass every count.
    --low)      int "${2:-}"; shift 2 ;;
    --weak)     int "${2:-}"; weak=$2; shift 2 ;;
    *) usage ;;
  esac
done

[ -n "$score" ] || usage
score=$((10#$score))
{ [ "$score" -ge 1 ] && [ "$score" -le 10 ]; } || usage

mw=$((medium + weak))
flag() { echo "FLAG: $1"; exit 1; }

if [ "$critical" -ge 1 ] && [ "$score" -gt 4 ]; then
  flag "score $score with $critical CRITICAL; a CRITICAL caps the score at 4 (band 3-4 or lower)"
elif [ "$high" -ge 1 ] && [ "$score" -gt 6 ]; then
  flag "score $score with $high HIGH; a HIGH caps the score at 6 (band 5-6 or lower)"
elif [ "$mw" -ge 3 ] && [ "$score" -gt 6 ]; then
  flag "score $score with $mw MEDIUM/WEAK; three or more cap the score at 6 (band 5-6 or lower)"
elif [ "$mw" -ge 1 ] && [ "$score" -gt 8 ]; then
  flag "score $score with $mw MEDIUM/WEAK; any cap the score at 8 (band 7-8 or lower)"
elif [ $((critical + high + mw)) -eq 0 ] && [ "$score" -lt 7 ]; then
  flag "score $score with no CRITICAL, HIGH, MEDIUM or WEAK findings; a clean domain scores 7 or more (band 7-8 or higher)"
fi
echo ok
