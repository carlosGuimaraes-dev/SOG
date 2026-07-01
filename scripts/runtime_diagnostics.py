#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared"))

from sog_shared.runtime_diagnostics import run_checks, write_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico de runtime local do SOG")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Valida pré-requisitos antes do `docker compose up`, sem exigir containers já iniciados.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Persiste o relatório em dados/support/runtime-diagnostic.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o relatório completo em JSON.",
    )
    args = parser.parse_args()

    report = run_checks(project_root=ROOT, include_container_runtime=not args.preflight)
    if args.write_report:
        write_report(report)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["operator_message"])
        print(report["support_summary"])
        for step in report["steps"]:
            print(f"- [{step['status']}] {step['label']}: {step['summary']}")

    return 0 if report["overall_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
