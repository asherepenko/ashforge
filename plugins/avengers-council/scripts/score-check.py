#!/usr/bin/env python3
"""score-check.py — flag a domain score that contradicts the member's own findings.

The domain score is informational, but a 9 next to an open HIGH is a lazy
score. These rules are first-match, top-down; the first match is the flag.

Usage:
  score-check.py --score N [--critical N] [--high N] [--medium N] [--low N] [--weak N]
--score is required (1-10). Other counts default to 0. LOW never flags.
Output: "ok", or "FLAG: <reason naming the band>"
Exit:   0 ok · 1 flag · 2 usage error
"""
import re
import sys


def usage():
    print("usage: score-check.py --score 1-10 [--critical N] [--high N] [--medium N] [--low N] [--weak N]",
          file=sys.stderr)
    sys.exit(2)


def count(value):
    if value is None or not re.fullmatch(r"[0-9]+", value):
        usage()
    return int(value)


def main(argv):
    score = None
    counts = {"--critical": 0, "--high": 0, "--medium": 0, "--weak": 0}
    i = 0
    while i < len(argv):
        flag = argv[i]
        value = argv[i + 1] if i + 1 < len(argv) else None
        if flag == "--score":
            score = count(value)
        elif flag in counts:
            counts[flag] = count(value)
        elif flag == "--low":
            # LOW never moves the check; accepted so callers can pass every count.
            count(value)
        else:
            usage()
        i += 2

    if score is None or not 1 <= score <= 10:
        usage()

    critical, high = counts["--critical"], counts["--high"]
    mw = counts["--medium"] + counts["--weak"]

    flag = None
    if critical >= 1 and score > 4:
        flag = f"score {score} with {critical} CRITICAL; a CRITICAL caps the score at 4 (band 3-4 or lower)"
    elif high >= 1 and score > 6:
        flag = f"score {score} with {high} HIGH; a HIGH caps the score at 6 (band 5-6 or lower)"
    elif mw >= 3 and score > 6:
        flag = f"score {score} with {mw} MEDIUM/WEAK; three or more cap the score at 6 (band 5-6 or lower)"
    elif mw >= 1 and score > 8:
        flag = f"score {score} with {mw} MEDIUM/WEAK; any cap the score at 8 (band 7-8 or lower)"
    elif critical + high + mw == 0 and score < 7:
        flag = (f"score {score} with no CRITICAL, HIGH, MEDIUM or WEAK findings; "
                "a clean domain scores 7 or more (band 7-8 or higher)")
    if flag:
        print(f"FLAG: {flag}")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
