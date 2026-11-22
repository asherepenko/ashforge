#!/usr/bin/env python3
"""risk-tier.py — compute the Risk row from what the change touches.

Captain America tags what the change touches from the fixed list below and
runs this script; the highest tier wins. The tier comes from the tags, never
from who wrote the change. See references/verdict-rules.md#risk.

Usage:
  risk-tier.py --touches TAG[,TAG...]
  risk-tier.py --list
Output: one line, e.g. "high — touches: auth, secrets"
Exit:   0 ok · 2 usage error (unknown or missing tag; prints nothing on stdout)
"""
import sys

TIERS = {
    "low": ["docs", "copy", "internal-tooling", "flagged-additive"],
    "medium": ["product"],
    "high": ["auth", "permissions", "billing", "payments", "data-migration",
             "ci-deploy", "release", "auto-update", "secrets", "two-person-path"],
}
ORDER = ["low", "medium", "high"]
TIER_OF = {tag: tier for tier, tags in TIERS.items() for tag in tags}


def usage():
    print("usage: risk-tier.py --touches TAG[,TAG...] | --list\ntags: "
          + ", ".join(TIER_OF), file=sys.stderr)
    sys.exit(2)


def main(argv):
    if argv == ["--list"]:
        for tier in ORDER:
            print(f"{tier}: {', '.join(TIERS[tier])}")
        return 0
    if len(argv) != 2 or argv[0] != "--touches":
        usage()
    tags = [t.strip() for t in argv[1].split(",") if t.strip()]
    if not tags or any(t not in TIER_OF for t in tags):
        usage()
    tier = max((TIER_OF[t] for t in tags), key=ORDER.index)
    named = [t for t in dict.fromkeys(tags) if TIER_OF[t] == tier]
    print(f"{tier} — touches: {', '.join(named)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
