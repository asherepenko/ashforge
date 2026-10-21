#!/usr/bin/env bash
# review-grade.sh — compute the Overall Grade line of /two-stage-review.
#
# The grade is defined as derived from counts, never judged, so it is code:
# the letter and the derivation after the dash come out the same for every
# reviewer and every runtime. Rules are first-match, top-down, as in SKILL.md.
#
# Usage:
#   review-grade.sh [--blocking N] [--optional N] [--nit N] [--fyi N]
#                   [--spec-open N] [--accepted-deviation]
#   review-grade.sh --ladder pr       [--critical N] [--important N] [--suggestion N] [--nit N] [--info N]
#   review-grade.sh --ladder severity [--critical N] [--high N] [--medium N] [--low N] [--info N]
# Without --ladder the two-stage rules apply. With --ladder, only that
# vocabulary's flags are valid; any other flag exits 2.
# Change size is not an input: a big diff is a Risk signal, not a quality defect.
# Output: one line, e.g.
#   Quality: B — 1 Optional, 2 Nit
#   Quality: D — 0 critical, 1 important, 0 suggestion, 0 nit
# Exit:   0 ok · 2 usage error

set -euo pipefail

usage() {
  echo "usage: review-grade.sh [--blocking N] [--optional N] [--nit N] [--fyi N] [--spec-open N] [--accepted-deviation]" >&2
  echo "       review-grade.sh --ladder pr|severity [count flags of that vocabulary] [--info N]" >&2
  exit 2
}

int() { [[ "${1:-}" =~ ^[0-9]+$ ]] || usage; }

blocking=0 optional=0 nit=0 spec=0 accepted=0
ladder="" critical=0 important=0 suggestion=0 high=0 medium=0 low=0 seen=" "
while [ $# -gt 0 ]; do
  seen+="$1 "
  case "$1" in
    --ladder)    ladder="${2:-}"; [ -n "$ladder" ] || usage; shift 2 ;;
    --critical)  int "${2:-}"; critical=$2; shift 2 ;;
    --important) int "${2:-}"; important=$2; shift 2 ;;
    --suggestion) int "${2:-}"; suggestion=$2; shift 2 ;;
    --high)      int "${2:-}"; high=$2; shift 2 ;;
    --medium)    int "${2:-}"; medium=$2; shift 2 ;;
    --low)       int "${2:-}"; low=$2; shift 2 ;;
    # INFO never moves the grade; accepted so callers can pass every count.
    --info)      int "${2:-}"; shift 2 ;;
    --blocking)  int "${2:-}"; blocking=$2; shift 2 ;;
    --optional)  int "${2:-}"; optional=$2; shift 2 ;;
    --nit)       int "${2:-}"; nit=$2; shift 2 ;;
    # FYI is accepted so callers can pass every count, but it never moves the grade.
    --fyi)       int "${2:-}"; shift 2 ;;
    --spec-open) int "${2:-}"; spec=$2; shift 2 ;;
    --accepted-deviation) accepted=1; shift ;;
    *) usage ;;
  esac
done

allowed=""
case "$ladder" in
  "")       allowed=" --blocking --optional --nit --fyi --spec-open --accepted-deviation " ;;
  pr)       allowed=" --ladder --critical --important --suggestion --nit --info " ;;
  severity) allowed=" --ladder --critical --high --medium --low --info " ;;
  *) usage ;;
esac
for f in $seen; do
  case "$allowed" in *" $f "*) ;; *) usage ;; esac
done

if [ "$ladder" = pr ]; then
  if [ "$critical" -gt 0 ]; then grade=F
  elif [ "$important" -gt 0 ]; then grade=D
  elif [ "$suggestion" -ge 3 ]; then grade=C
  elif [ "$suggestion" -ge 1 ] || [ "$nit" -gt 3 ]; then grade=B
  else grade=A
  fi
  echo "Quality: $grade — $critical critical, $important important, $suggestion suggestion, $nit nit"
  exit 0
elif [ "$ladder" = severity ]; then
  if [ "$critical" -gt 0 ]; then grade=F
  elif [ "$high" -gt 0 ]; then grade=D
  elif [ "$medium" -ge 3 ]; then grade=C
  elif [ "$medium" -ge 1 ] || [ "$low" -gt 3 ]; then grade=B
  else grade=A
  fi
  echo "Quality: $grade — $critical critical, $high high, $medium medium, $low low"
  exit 0
fi

if [ "$blocking" -gt 0 ]; then
  echo "Quality: F (blocked) — $blocking BLOCKING open; Stage 2 not run"
  exit 0
fi

if [ "$accepted" -eq 1 ]; then grade=D
elif [ "$optional" -ge 3 ] || [ "$spec" -gt 0 ]; then grade=C
elif [ "$optional" -ge 1 ] || [ "$nit" -gt 3 ]; then grade=B
else grade=A
fi

derivation="$optional Optional, $nit Nit"
if [ "$spec" -eq 1 ]; then derivation+=", 1 open spec finding"
elif [ "$spec" -gt 1 ]; then derivation+=", $spec open spec findings"
fi
if [ "$accepted" -eq 1 ]; then derivation+=", accepted deviation"; fi
echo "Quality: $grade — $derivation"
