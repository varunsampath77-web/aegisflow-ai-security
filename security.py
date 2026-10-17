
import json
import re
from pathlib import Path

POLICY_FILE = Path(__file__).with_name("policies.json")

with POLICY_FILE.open("r", encoding="utf-8") as file:
    POLICIES = json.load(file)

# Basic rule-based prompt-injection detector
SUSPICIOUS_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"reveal (the )?(system prompt|secret|password)",
    r"send .* to .*external",
    r"bypass (the )?security",
    r"disregard (all )?(previous|prior) instructions",
    r"transfer funds",
]


def detect_injection(content):
    text = content.lower()

    matches = [
        pattern
        for pattern in SUSPICIOUS_PATTERNS
        if re.search(pattern, text)
    ]

    return {
        "suspicious": bool(matches),
        "matched_rules": matches,
    }


def evaluate_request(agent, action, content):
    policy = POLICIES.get(agent)

    if policy is None:
        return {
            "decision": "BLOCK",
            "risk_score": 100,
            "reason": "Unknown agent",
        }

    detection = detect_injection(content)

    if action in policy["denied_actions"]:
        return {
            "decision": "BLOCK",
            "risk_score": 100,
            "reason": "Action denied by policy",
        }

    permitted_actions = (
        policy["allowed_actions"] + policy["review_actions"]
    )

    if action not in permitted_actions:
        return {
            "decision": "BLOCK",
            "risk_score": 90,
            "reason": "Action not explicitly permitted",
        }

    if detection["suspicious"]:
        return {
            "decision": "BLOCK",
            "risk_score": 90,
            "reason": "Suspicious instructions detected",
        }

    if action in policy["review_actions"]:
        return {
            "decision": "REVIEW",
            "risk_score": 60,
            "reason": "Human approval required",
        }

    return {
        "decision": "ALLOW",
        "risk_score": 0,
        "reason": "Policy permitted the action",
    }
