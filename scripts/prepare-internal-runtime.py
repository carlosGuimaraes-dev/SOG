#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared"))

from sog_shared.runtime_preparation import run_preparation_flow  # noqa: E402


def _print_text_result(result: dict) -> None:
    report = result["report"]
    state = result.get("state")

    print(f"Status do preparo: {result['status']}")
    print(report["operator_message"])
    print(report["support_summary"])

    if result.get("resume_message"):
        print(result["resume_message"])

    if result.get("uac_message"):
        print(result["uac_message"])

    if result["guidance"]:
        print("Ações oficiais recomendadas:")
        for item in result["guidance"]:
            print(f"- {item['label']}: {item['summary']}")
            print(f"  Fonte oficial: {item['official_source']}")
            if item["requires_elevation"]:
                print("  Elevação/UAC: esta etapa pode exigir privilégios administrativos.")
            if item["reboot_expected"]:
                print("  Retomada: reinicie o host após concluir esta etapa e rode o script novamente.")

    if state:
        print(f"Estado persistido em: {state['state_path']}")
    print(f"Relatório persistido em: {result['report_path']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preparo assistido do runtime interno do SOG")
    parser.add_argument("--json", action="store_true", help="Imprime o resultado completo em JSON.")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Não pergunta autorização no terminal; exige SOG_RUNTIME_PREP_AUTHORIZATION no ambiente.",
    )
    args = parser.parse_args()

    result = run_preparation_flow(
        project_root=ROOT,
        interactive=not args.non_interactive,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_text_result(result)

    if result["status"] == "ready":
        return 0
    if result["status"] == "awaiting_authorization":
        return 2
    if result["status"] == "awaiting_reboot":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
