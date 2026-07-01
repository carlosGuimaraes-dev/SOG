"""
Fluxo HITL para preparo assistido do runtime local do SOG.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .runtime_diagnostics import (
    clear_preparation_state,
    load_preparation_state,
    run_checks,
    write_preparation_state,
    write_report,
)

PromptFn = Callable[[str], str]

AUTHORIZATION_ENV = "SOG_RUNTIME_PREP_AUTHORIZATION"

DEPENDENCY_GUIDANCE = {
    "node": {
        "label": "Node.js",
        "official_source": "https://nodejs.org/en/download",
        "install_type": "manual",
        "requires_elevation": False,
        "reboot_expected": False,
        "summary": "Instale a versão LTS oficial do Node.js. O npm deve vir junto nesse instalador.",
    },
    "npm": {
        "label": "npm",
        "official_source": "https://docs.npmjs.com/downloading-and-installing-node-js-and-npm",
        "install_type": "manual",
        "requires_elevation": False,
        "reboot_expected": False,
        "summary": "Use as instruções oficiais do npm quando ele não vier junto com o Node.js já instalado.",
    },
    "docker": {
        "label": "Docker CLI",
        "official_source": "https://docs.docker.com/engine/install/",
        "install_type": "manual",
        "requires_elevation": False,
        "reboot_expected": False,
        "summary": "Instale o Docker Engine/CLI oficial. O fluxo do SOG não usa Docker Desktop como jornada principal.",
    },
    "wsl": {
        "label": "WSL",
        "official_source": "https://learn.microsoft.com/windows/wsl/install",
        "install_type": "manual_elevated",
        "requires_elevation": True,
        "reboot_expected": True,
        "summary": "Habilite o WSL pelas instruções oficiais da Microsoft. Essa etapa pode exigir UAC e reinicialização.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _report_file(project_root: Path) -> Path:
    return project_root / "dados" / "support" / "runtime-diagnostic.json"


def _state_file(project_root: Path) -> Path:
    return project_root / "dados" / "support" / "runtime-preparation-state.json"


def _dependency_ids_requiring_action(report: Mapping[str, Any]) -> List[str]:
    pending: List[str] = []
    for step in report.get("steps", []):
        step_id = step.get("id")
        if step_id in DEPENDENCY_GUIDANCE and step.get("status") in {"warning", "error"}:
            pending.append(step_id)
    return pending


def _guidance_for_dependencies(dependency_ids: Iterable[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for dependency_id in dependency_ids:
        guidance = DEPENDENCY_GUIDANCE[dependency_id]
        items.append({
            "id": dependency_id,
            **guidance,
        })
    return items


def _resolve_authorization(env: Mapping[str, str], prompt: PromptFn, interactive: bool) -> str:
    env_value = env.get(AUTHORIZATION_ENV, "").strip().lower()
    if env_value in {"approved", "yes", "y", "true", "1"}:
        return "approved"
    if env_value in {"denied", "no", "n", "false", "0"}:
        return "denied"
    if not interactive:
        return "needs_input"
    answer = prompt(
        "Dependências ausentes exigem autorização do operador para continuar com a preparação local. "
        "Autoriza seguir para as instruções oficiais? [s/N]: "
    ).strip().lower()
    return "approved" if answer in {"s", "sim", "y", "yes"} else "denied"


def _build_state(
    *,
    project_root: Path,
    report: Mapping[str, Any],
    phase: str,
    dependency_ids: List[str],
    authorization_status: str,
    previous_state: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "version": 1,
        "updated_at": _now(),
        "phase": phase,
        "authorization_status": authorization_status,
        "pending_dependencies": dependency_ids,
        "report_path": str(_report_file(project_root)),
        "state_path": str(_state_file(project_root)),
        "project_root": str(project_root),
        "previous_phase": previous_state.get("phase") if previous_state else None,
    }


def run_preparation_flow(
    *,
    project_root: Path,
    env: Optional[Mapping[str, str]] = None,
    prompt: Optional[PromptFn] = None,
    interactive: Optional[bool] = None,
) -> Dict[str, Any]:
    source_env = dict(env or os.environ)
    prompt_fn = prompt or input
    should_prompt = interactive if interactive is not None else os.isatty(0)

    report_file = _report_file(project_root)
    state_file = _state_file(project_root)

    report = run_checks(project_root=project_root, env=source_env)
    write_report(report, report_file)

    previous_state = load_preparation_state(state_file)
    dependency_ids = _dependency_ids_requiring_action(report)
    guidance = _guidance_for_dependencies(dependency_ids)

    if not dependency_ids:
        resumed = bool(previous_state)
        clear_preparation_state(state_file)
        return {
            "status": "ready",
            "report": report,
            "guidance": [],
            "state": None,
            "authorization_status": "not_needed",
            "resumed_after_reboot": resumed,
            "report_path": str(report_file),
            "state_path": str(state_file),
            "resume_message": (
                "Retomada concluída após reinicialização; nenhum pré-requisito pendente permanece."
                if resumed
                else None
            ),
        }

    authorization_status = _resolve_authorization(source_env, prompt_fn, should_prompt)
    if authorization_status != "approved":
        phase = "awaiting_authorization"
        state = _build_state(
            project_root=project_root,
            report=report,
            phase=phase,
            dependency_ids=dependency_ids,
            authorization_status=authorization_status,
            previous_state=previous_state,
        )
        write_preparation_state(state, state_file)
        return {
            "status": "awaiting_authorization",
            "report": report,
            "guidance": guidance,
            "state": state,
            "authorization_status": authorization_status,
            "resumed_after_reboot": False,
            "report_path": str(report_file),
            "state_path": str(state_file),
            "resume_message": None,
        }

    requires_elevation = any(item["requires_elevation"] for item in guidance)
    reboot_required = any(item["reboot_expected"] for item in guidance)
    phase = "awaiting_reboot" if reboot_required else "awaiting_manual_completion"
    state = _build_state(
        project_root=project_root,
        report=report,
        phase=phase,
        dependency_ids=dependency_ids,
        authorization_status=authorization_status,
        previous_state=previous_state,
    )
    write_preparation_state(state, state_file)

    uac_message = None
    if requires_elevation:
        uac_message = (
            "Antes de qualquer UAC: o SOG só deve solicitar elevação para concluir a etapa oficial do WSL. "
            "Revise a origem oficial, confirme que a instalação é necessária e então aceite a elevação no host."
        )

    return {
        "status": phase,
        "report": report,
        "guidance": guidance,
        "state": state,
        "authorization_status": authorization_status,
        "resumed_after_reboot": bool(previous_state and previous_state.get("phase") == "awaiting_reboot"),
        "report_path": str(report_file),
        "state_path": str(state_file),
        "resume_message": (
            "Fluxo retomado a partir de um reboot pendente anterior."
            if previous_state and previous_state.get("phase") == "awaiting_reboot"
            else None
        ),
        "uac_message": uac_message,
        "reboot_required": reboot_required,
    }
