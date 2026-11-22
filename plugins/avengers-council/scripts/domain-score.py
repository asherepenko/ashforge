#!/usr/bin/env python3
"""domain-score.py — compute a member's domain score from their own findings.

Members never pick the score. The orchestrator counts the member's own
findings (code reviews: `Introduced here: yes` only) and WEAK criteria and runs
this script, so the score is the same for every reviewer and every runtime.
Rules are first-match, top-down, as in references/verdict-rules.md#domain-scoring.
MW = MEDIUM + WEAK. LOW never lowers the score.

  2+ CRITICAL                 -> 1
  1 CRITICAL                  -> 3
  2+ HIGH, or 1 HIGH + 3+ MW  -> 5
  1 HIGH, or 3+ MW            -> 6
  2 MW                        -> 7
  1 MW                        -> 8
  none of the above           -> 10

Usage:
  domain-score.py [--critical N] [--high N] [--medium N] [--low N] [--weak N]
  domain-score.py --average SCORE...   (each SCORE is N/10 or n/a)
Output: one line, e.g. "6/10", "6.3/10" or "n/a"
Exit:   0 ok · 2 usage error (prints nothing on stdout)
"""
import re
import sys


def usage():
    print("usage: domain-score.py [--critical N] [--high N] [--medium N] [--low N] [--weak N]\n"
          "       domain-score.py --average SCORE...  (N/10 or n/a)", file=sys.stderr)
    sys.exit(2)


def count(value):
    if value is None or not re.fullmatch(r"[0-9]+", value):
        usage()
    return int(value)


def compute(critical, high, mw):
    if critical >= 2:
        return 1
    if critical == 1:
        return 3
    if high >= 2 or (high == 1 and mw >= 3):
        return 5
    if high == 1 or mw >= 3:
        return 6
    if mw == 2:
        return 7
    if mw == 1:
        return 8
    return 10


def average(values):
    scores = []
    for v in values:
        if v == "n/a":
            continue
        m = re.fullmatch(r"([1-9]|10)/10", v)
        if not m:
            usage()
        scores.append(int(m.group(1)))
    if not scores:
        return "n/a"
    return f"{sum(scores) / len(scores):.1f}/10"


def main(argv):
    if argv and argv[0] == "--average":
        if len(argv) < 2:
            usage()
        print(average(argv[1:]))
        return 0
    counts = {"--critical": 0, "--high": 0, "--medium": 0, "--low": 0, "--weak": 0}
    seen = set()
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag not in counts or flag in seen:
            usage()
        seen.add(flag)
        counts[flag] = count(argv[i + 1] if i + 1 < len(argv) else None)
        i += 2
    mw = counts["--medium"] + counts["--weak"]
    print(f"{compute(counts['--critical'], counts['--high'], mw)}/10")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
