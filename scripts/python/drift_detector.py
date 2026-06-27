#!/usr/bin/env python3
"""
drift_detector.py
-----------------
Runs ansible-playbook in check mode against a given inventory
and parses the output to count how many tasks *would* change.

If the number of changed tasks exceeds the threshold, exits non-zero
so CI/CD pipelines can alert on configuration drift.

Usage:
    python3 scripts/python/drift_detector.py \\
        --inventory inventory/production \\
        --threshold 5

Exit codes:
    0 — No drift (or drift within threshold)
    1 — Drift detected above threshold
    2 — Ansible execution error
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect Ansible configuration drift.")
    parser.add_argument("--inventory", required=True, help="Path to inventory directory")
    parser.add_argument("--playbook", default="playbooks/site.yml", help="Playbook to check")
    parser.add_argument("--threshold", type=int, default=0, help="Max allowed changed tasks")
    parser.add_argument("--vault-password-file", default=None, help="Path to vault password file")
    parser.add_argument("--output-json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def run_check_mode(inventory: str, playbook: str, vault_file: str | None) -> tuple[int, str, str]:
    cmd = [
        "ansible-playbook",
        "-i", inventory,
        playbook,
        "--check",
        "--diff",
        "-v",
    ]
    if vault_file:
        cmd.extend(["--vault-password-file", vault_file])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def parse_recap(output: str) -> dict[str, dict[str, int]]:
    """Parse the PLAY RECAP section from ansible-playbook output."""
    recap: dict[str, dict[str, int]] = {}
    in_recap = False

    for line in output.splitlines():
        if "PLAY RECAP" in line:
            in_recap = True
            continue
        if in_recap and line.strip():
            # Format: hostname : ok=N changed=N unreachable=N failed=N
            parts = line.split()
            if len(parts) >= 6 and ":" in parts[1]:
                host = parts[0]
                stats: dict[str, int] = {}
                for part in parts[2:]:
                    if "=" in part:
                        key, val = part.split("=")
                        stats[key] = int(val)
                recap[host] = stats

    return recap


def main() -> int:
    args = parse_args()
    timestamp = datetime.utcnow().isoformat()

    print(f"[{timestamp}] Running drift detection against {args.inventory}...", flush=True)

    returncode, stdout, stderr = run_check_mode(args.inventory, args.playbook, args.vault_password_file)

    if returncode not in (0, 2):  # 2 = some hosts failed, but we still got recap
        print(f"ERROR: ansible-playbook exited with code {returncode}", file=sys.stderr)
        print(stderr, file=sys.stderr)
        return 2

    recap = parse_recap(stdout)

    if not recap:
        print("WARNING: Could not parse PLAY RECAP. Check ansible output manually.")
        print(stdout)
        return 2

    total_changed = sum(h.get("changed", 0) for h in recap.values())
    total_failed = sum(h.get("failed", 0) for h in recap.values())
    total_unreachable = sum(h.get("unreachable", 0) for h in recap.values())

    result = {
        "timestamp": timestamp,
        "inventory": args.inventory,
        "threshold": args.threshold,
        "total_changed": total_changed,
        "total_failed": total_failed,
        "total_unreachable": total_unreachable,
        "drift_detected": total_changed > args.threshold,
        "hosts": recap,
    }

    if args.output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"  Drift Detection Report — {timestamp}")
        print(f"{'='*50}")
        print(f"  Inventory : {args.inventory}")
        print(f"  Threshold : {args.threshold} tasks")
        print(f"  Changed   : {total_changed} tasks")
        print(f"  Failed    : {total_failed} hosts")
        print(f"  Unreachable: {total_unreachable} hosts")
        print(f"{'='*50}")

        for host, stats in recap.items():
            changed = stats.get("changed", 0)
            status = "DRIFT" if changed > 0 else "OK"
            print(f"  [{status:5}] {host} — {changed} tasks would change")

        print(f"{'='*50}")

        if total_changed > args.threshold:
            print(f"\nDRIFT DETECTED: {total_changed} tasks would change (threshold: {args.threshold})")
            print("Run the playbook to remediate: ansible-playbook -i "
                  f"{args.inventory} {args.playbook}")
        else:
            print(f"\nNo significant drift detected ({total_changed} tasks within threshold).")

    return 1 if total_changed > args.threshold else 0


if __name__ == "__main__":
    sys.exit(main())
