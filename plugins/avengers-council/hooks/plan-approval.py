#!/usr/bin/env python3
"""Bind council approval to the hook's session, plan path, and exact content."""
import argparse
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
import sys
import uuid


def digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def state_path(cwd, session):
    return Path(cwd) / ".artifacts/tmp/council-plan" / (digest(session) + ".json")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(path)


def transcript_result(payload, pending):
    if not valid_token(pending.get("token")):
        return None
    transcript = payload.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return None
    latest = None
    with Path(transcript).open(encoding="utf-8") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if (event.get("type") != "assistant" or event.get("sessionId") != pending["session"]
                    or event.get("isSidechain", False)):
                continue
            message = event.get("message", {})
            if message.get("role") != "assistant":
                continue
            for block in message.get("content", []):
                if not isinstance(block, dict) or block.get("type") != "text":
                    continue
                for text in block.get("text", "").splitlines():
                    if not text.startswith("COUNCIL_PLAN_REVIEW_RESULT "):
                        continue
                    try:
                        receipt = json.loads(text[len("COUNCIL_PLAN_REVIEW_RESULT "): ])
                    except ValueError:
                        continue
                    if (isinstance(receipt, dict) and all(receipt.get(k) == pending.get(k)
                            for k in ("session", "plan", "digest", "token"))
                            and receipt.get("verdict") in ("APPROVED", "APPROVED WITH CONDITIONS", "NEEDS REVISION", "BLOCKED")
                            and isinstance(receipt.get("review"), str) and receipt["review"].strip()):
                        latest = receipt
    return latest


def valid_token(token):
    return isinstance(token, str) and re.fullmatch(r"[0-9a-f]{32}", token) is not None


def check(payload):
    session, cwd = payload.get("session_id"), payload.get("cwd")
    tool = payload.get("tool_input", {})
    plan, content = tool.get("planFilePath"), tool.get("plan")
    if not all(isinstance(v, str) and v for v in (session, cwd, plan, content)):
        return False, "Missing session_id, cwd, or injected plan/planFilePath; approval cannot be verified."
    source = Path(plan).resolve()
    if source.read_text(encoding="utf-8") != content:
        return False, "Injected plan differs from its file; review the current plan before retrying."
    path = state_path(cwd, session)
    identity = {"session": session, "plan": str(source), "digest": digest(content)}
    previous = json.loads(path.read_text()) if path.exists() else {}
    if (not isinstance(previous, dict) or not valid_token(previous.get("token"))
            or not all(previous.get(k) == v for k, v in identity.items())):
        previous = dict(identity, token=uuid.uuid4().hex)
    save(path, previous)
    receipt = transcript_result(payload, previous)
    if receipt:
        # Hooks can persist reviews while the reviewing session is read-only.
        stamp = datetime.now().astimezone()
        slug = receipt["verdict"].lower().replace(" ", "-")
        review_root = Path(cwd) / ".artifacts/reviews/plans/council"
        review_dir = review_root / stamp.strftime("%Y-%m-%d")
        filename = stamp.strftime("%H%M%S") + f"-review-{slug}-{digest(session)[:12]}.md"
        # Reuse only our own generated basename under the current project bucket.
        saved = previous.get("review_file")
        if (saved and previous.get("verdict") == receipt["verdict"]
                and previous.get("review") == receipt["review"]
                and len(Path(saved).parts) == 2
                and all(part not in (".", "..") for part in Path(saved).parts)
                and not Path(saved).is_absolute()):
            review_path = review_root / saved
        else:
            review_path = review_dir / filename
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(f"# Council verdict: {receipt['verdict']}\n\n{receipt['review']}\n", encoding="utf-8")
        save(path, dict(receipt, review_file=str(review_path.relative_to(review_root))))
        if receipt["verdict"] in ("APPROVED", "APPROVED WITH CONDITIONS"):
            return True, ""
    template = dict(identity, token=previous["token"], verdict="<final verdict>", review="<full synthesized review markdown>")
    return False, ("Council review required before proceeding. Invoke council-plan-review for "
                   f"{source}. Do not continue until review is complete. In plan mode, emit this "
                   "receipt as a standalone assistant-text line after synthesis, before follow-up; "
                   "the hook saves the review on the next ExitPlanMode call. Replace only verdict and review:\n"
                   "COUNCIL_PLAN_REVIEW_RESULT " + json.dumps(template))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("check",))
    args = parser.parse_args()
    try:
        allowed, reason = check(json.load(sys.stdin))
        if not allowed:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": reason, "additionalContext": reason,
            }}))
        return 0
    except (OSError, ValueError, TypeError, AttributeError) as error:
        if args.operation == "check":
            reason = f"Council approval cannot be verified: {error}. Invoke council-plan-review before proceeding; do not continue until review is complete."
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": reason, "additionalContext": reason}}))
            return 0


if __name__ == "__main__":
    sys.exit(main())
