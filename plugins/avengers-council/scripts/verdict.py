#!/usr/bin/env python3
"""verdict.py — compute the council verdict from votes and finding counts.

Captain America never applies the consensus rules by hand. He counts the
final votes and the findings (code reviews: `Introduced here: yes` only),
runs this script and pastes the line. Rules are first-match, top-down, as in
references/verdict-rules.md. N = approve + concerns + reject.

Full mode (majority = floor(N/2)+1, block = max(1, floor(N*0.45))):
  BLOCKED                   veto, or reject >= block, or 2+ standards
  NEEDS REVISION            reject >= 2, or any critical, red line, standard or missing AC
  APPROVED                  approve >= majority, 0 reject, 0 HIGH
  APPROVED WITH CONDITIONS  approve >= majority - 1 (every HIGH is a condition)
  NO CONSENSUS              anything else: apply the tiebreaker
Quick mode (N must be 3):
  BLOCKED                   veto, or any reject
  NEEDS REVISION            concerns >= 2, or any critical, red line, standard or missing AC
  APPROVED                  3 approve, 0 HIGH
  APPROVED WITH CONDITIONS  otherwise (2 approve + 1 concerns, or HIGH present)

Usage:
  verdict.py --mode full|quick --approve N --concerns N --reject N
             [--critical N] [--high N] [--red-lines N] [--standards N]
             [--missing-ac N] [--veto]
  --missing-ac: plan reviews, count of major acceptance criteria missing
Output: one line, e.g. "APPROVED WITH CONDITIONS — 2 HIGH as conditions"
Exit:   0 ok · 2 usage error (prints nothing on stdout)
"""
import re
import sys

COUNTS = ["--approve", "--concerns", "--reject", "--critical", "--high", "--red-lines", "--standards",
          "--missing-ac"]


def usage():
    print(__doc__.split("Usage:")[1].split("Output:")[0].rstrip(), file=sys.stderr)
    sys.exit(2)


def parse(argv):
    mode, veto, c = None, False, {k: None for k in COUNTS}
    seen = set()
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag in seen:
            usage()
        seen.add(flag)
        if flag == "--veto":
            veto = True
            i += 1
            continue
        value = argv[i + 1] if i + 1 < len(argv) else None
        if flag == "--mode" and value in ("full", "quick"):
            mode = value
        elif flag in c and value is not None and re.fullmatch(r"[0-9]+", value):
            c[flag] = int(value)
        else:
            usage()
        i += 2
    if mode is None or any(c[k] is None for k in COUNTS[:3]):
        usage()
    c = {k[2:].replace("-", "_"): (v or 0) for k, v in c.items()}
    return mode, veto, c


def conditions(c):
    return f"APPROVED WITH CONDITIONS — {c['high']} HIGH as conditions"


def revision_reason(c, concerns_rule):
    if concerns_rule:
        return f"{c['concerns']} CONCERNS votes"
    if c["reject"] >= 2:
        return f"{c['reject']} REJECT votes"
    if c["critical"]:
        return f"{c['critical']} unmitigated CRITICAL"
    if c["red_lines"]:
        return f"{c['red_lines']} red line violation(s)"
    if c["missing_ac"]:
        return f"{c['missing_ac']} missing acceptance criteria"
    return f"{c['standards']} mandatory standard violation"


def full(veto, c):
    n = c["approve"] + c["concerns"] + c["reject"]
    if n == 0:
        usage()
    majority, block = n // 2 + 1, max(1, int(n * 0.45))
    if veto:
        return "BLOCKED — Black Widow veto"
    if c["reject"] >= block:
        return f"BLOCKED — {c['reject']} REJECT votes (threshold {block} of {n})"
    if c["standards"] >= 2:
        return f"BLOCKED — {c['standards']} mandatory standard violations"
    if c["reject"] >= 2 or c["critical"] or c["red_lines"] or c["standards"] or c["missing_ac"]:
        return "NEEDS REVISION — " + revision_reason(c, False)
    if c["approve"] >= majority and c["reject"] == 0 and c["high"] == 0:
        return "APPROVED"
    if c["approve"] >= majority - 1:
        return conditions(c)
    return f"NO CONSENSUS — {c['approve']} APPROVE of {n}, majority {majority}: apply the tiebreaker"


def quick(veto, c):
    if c["approve"] + c["concerns"] + c["reject"] != 3:
        usage()
    if veto:
        return "BLOCKED — Black Widow veto"
    if c["reject"]:
        return f"BLOCKED — {c['reject']} REJECT vote"
    if c["concerns"] >= 2:
        return "NEEDS REVISION — " + revision_reason(c, True)
    if c["critical"] or c["red_lines"] or c["standards"] or c["missing_ac"]:
        return "NEEDS REVISION — " + revision_reason(c, False)
    if c["approve"] == 3 and c["high"] == 0:
        return "APPROVED"
    return conditions(c)


def main(argv):
    mode, veto, c = parse(argv)
    print(full(veto, c) if mode == "full" else quick(veto, c))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
