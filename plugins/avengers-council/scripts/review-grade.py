#!/usr/bin/env python3
"""review-grade.py — compute the Overall Grade line of /two-stage-review.

The grade is defined as derived from counts, never judged, so it is code:
the letter and the derivation after the dash come out the same for every
reviewer and every runtime. Rules are first-match, top-down, as in SKILL.md.

Usage:
  review-grade.py [--blocking N] [--optional N] [--nit N] [--fyi N]
                  [--spec-open N] [--accepted-deviation]
  review-grade.py --ladder pr       [--critical N] [--important N] [--suggestion N] [--nit N] [--info N]
  review-grade.py --ladder severity [--critical N] [--high N] [--medium N] [--low N] [--info N]
Without --ladder the two-stage rules apply. With --ladder, only that
vocabulary's flags are valid; any other flag exits 2.
Change size is not an input: a big diff is a Risk signal, not a quality defect.
Output: one line, e.g.
  Quality: B — 1 Optional, 2 Nit
  Quality: D — 0 critical, 1 important, 0 suggestion, 0 nit
Exit:   0 ok · 2 usage error
"""
import re
import sys


def usage():
    print("usage: review-grade.py [--blocking N] [--optional N] [--nit N] [--fyi N] [--spec-open N] [--accepted-deviation]",
          file=sys.stderr)
    print("       review-grade.py --ladder pr|severity [count flags of that vocabulary] [--info N]", file=sys.stderr)
    sys.exit(2)


# INFO and FYI never move the grade; accepted so callers can pass every count.
COUNT_FLAGS = {
    "--critical": "critical", "--important": "important", "--suggestion": "suggestion",
    "--high": "high", "--medium": "medium", "--low": "low", "--info": None,
    "--blocking": "blocking", "--optional": "optional", "--nit": "nit", "--fyi": None,
    "--spec-open": "spec",
}
ALLOWED = {
    "": {"--blocking", "--optional", "--nit", "--fyi", "--spec-open", "--accepted-deviation"},
    "pr": {"--ladder", "--critical", "--important", "--suggestion", "--nit", "--info"},
    "severity": {"--ladder", "--critical", "--high", "--medium", "--low", "--info"},
}


def main(argv):
    n = dict.fromkeys(["blocking", "optional", "nit", "spec", "critical", "important",
                       "suggestion", "high", "medium", "low"], 0)
    ladder = ""
    accepted = False
    seen = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        value = argv[i + 1] if i + 1 < len(argv) else None
        seen.append(flag)
        if flag == "--ladder":
            ladder = value or ""
            if not ladder:
                usage()
            i += 2
        elif flag in COUNT_FLAGS:
            if value is None or not re.fullmatch(r"[0-9]+", value):
                usage()
            if COUNT_FLAGS[flag]:
                n[COUNT_FLAGS[flag]] = int(value)
            i += 2
        elif flag == "--accepted-deviation":
            accepted = True
            i += 1
        else:
            usage()

    if ladder not in ALLOWED:
        usage()
    if any(f not in ALLOWED[ladder] for f in seen):
        usage()

    if ladder == "pr":
        if n["critical"] > 0:
            grade = "F"
        elif n["important"] > 0:
            grade = "D"
        elif n["suggestion"] >= 3:
            grade = "C"
        elif n["suggestion"] >= 1 or n["nit"] > 3:
            grade = "B"
        else:
            grade = "A"
        line = f"Quality: {grade} — {n['critical']} critical, {n['important']} important, {n['suggestion']} suggestion, {n['nit']} nit"
    elif ladder == "severity":
        if n["critical"] > 0:
            grade = "F"
        elif n["high"] > 0:
            grade = "D"
        elif n["medium"] >= 3:
            grade = "C"
        elif n["medium"] >= 1 or n["low"] > 3:
            grade = "B"
        else:
            grade = "A"
        line = f"Quality: {grade} — {n['critical']} critical, {n['high']} high, {n['medium']} medium, {n['low']} low"
    elif n["blocking"] > 0:
        line = f"Quality: F (blocked) — {n['blocking']} BLOCKING open; Stage 2 not run"
    else:
        if accepted:
            grade = "D"
        elif n["optional"] >= 3 or n["spec"] > 0:
            grade = "C"
        elif n["optional"] >= 1 or n["nit"] > 3:
            grade = "B"
        else:
            grade = "A"
        derivation = f"{n['optional']} Optional, {n['nit']} Nit"
        if n["spec"] == 1:
            derivation += ", 1 open spec finding"
        elif n["spec"] > 1:
            derivation += f", {n['spec']} open spec findings"
        if accepted:
            derivation += ", accepted deviation"
        line = f"Quality: {grade} — {derivation}"

    sys.stdout.buffer.write((line + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
