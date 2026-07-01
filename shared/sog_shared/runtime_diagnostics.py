"""
Utilitários para relatórios de diagnóstico de runtime voltados a suporte.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from .config import DB_PATH

SUPPORT_PHONE_ENV = "SUPPORT_PHONE"
SUPPORT_EMAIL_ENV = "SUPPORT_EMAIL"
SUPPORT_PHONE_PLACEHOLDER = "+1 (425) 548-4969"
SUPPORT_EMAIL_PLACEHOLDER = "guimaraes.dpf@gmail.com"
REPORT_RELATIVE_PATH = Path("support") / "runtime-diagnostic.json"
PREPARATION_STATE_RELATIVE_PATH = Path("support") / "runtime-preparation-state.json"

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def support_contact(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env or os.environ
    phone = source.get(SUPPORT_PHONE_ENV, SUPPORT_PHONE_PLACEHOLDER).strip() or SUPPORT_PHONE_PLACEHOLDER
    email = source.get(SUPPORT_EMAIL_ENV, SUPPORT_EMAIL_PLACEHOLDER).strip() or SUPPORT_EMAIL_PLACEHOLDER
    return {
        "phone": phone,
        "email": email,
        "is_placeholder": False,
    }


def report_path(db_path: Optional[str] = None) -> Path:
    base = Path(db_path or DB_PATH).expanduser().resolve().parent
    return base / REPORT_RELATIVE_PATH


def preparation_state_path(db_path: Optional[str] = None) -> Path:
    base = Path(db_path or DB_PATH).expanduser().resolve().parent
    return base / PREPARATION_STATE_RELATIVE_PATH


def load_report(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    resolved = path or report_path()
    if not resolved.exists():
        return None
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_report(report: Dict[str, Any], path: Optional[Path] = None) -> Path:
    resolved = path or report_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return resolved


def load_preparation_state(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    resolved = path or preparation_state_path()
    if not resolved.exists():
        return None
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_preparation_state(state: Dict[str, Any], path: Optional[Path] = None) -> Path:
    resolved = path or preparation_state_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return resolved


def clear_preparation_state(path: Optional[Path] = None) -> None:
    resolved = path or preparation_state_path()
    try:
        resolved.unlink()
    except FileNotFoundError:
        return
    except OSError:
        return


def build_operator_message(report: Mapping[str, Any]) -> str:
    if report.get("overall_status") == "ok":
        return "Runtime local do SOG verificado sem falhas bloqueantes."
    contact = report.get("support_contact") or {}
    phone = contact.get("phone", SUPPORT_PHONE_PLACEHOLDER)
    email = contact.get("email", SUPPORT_EMAIL_PLACEHOLDER)
    failing_step = report.get("failing_step_label") or "preparo do ambiente"
    return (
        "Falha na preparação/local startup do SOG. "
        f"Entre em contato com o suporte em {phone} ou {email} "
        f"e informe que o diagnóstico identificou problema em: {failing_step}."
    )


def build_support_summary(report: Mapping[str, Any]) -> str:
    if report.get("overall_status") == "ok":
        return "Sem falhas bloqueantes no runtime local."
    failing_step = report.get("failing_step_label") or "indeterminado"
    summary = report.get("summary") or "Sem resumo adicional."
    return f"Etapa com falha: {failing_step}. {summary}"


def run_checks(
    *,
    project_root: Path,
    env: Optional[Mapping[str, str]] = None,
    command_runner: Optional[CommandRunner] = None,
    include_container_runtime: bool = True,
) -> Dict[str, Any]:
    source_env = dict(env or os.environ)
    runner = command_runner or _default_runner
    compose_cmd = _detect_compose_command(runner)
    steps = [
        _check_command("node", ["node", "--version"], "Node.js", required=False, runner=runner),
        _check_command("npm", ["npm", "--version"], "npm", required=False, runner=runner),
        _check_command("docker", ["docker", "--version"], "Docker CLI", required=True, runner=runner),
        _check_compose(compose_cmd, runner),
        _check_docker_daemon(runner),
        _check_wsl(source_env, runner),
        _check_path(project_root / ".env.api", ".env.api"),
        _check_path(project_root / ".env.agente", ".env.agente"),
        _check_path(project_root / "dados", "Diretório dados"),
        _check_path(project_root / "dados" / "auth", "Diretório auth"),
        _check_path(project_root / "dados" / "screenshots", "Diretório screenshots"),
        _check_path(project_root / "dados" / "demonstrativos", "Diretório demonstrativos"),
        _check_compose_config(project_root, compose_cmd, runner),
    ]
    if include_container_runtime:
        steps.append(_check_containers_running(project_root, compose_cmd, runner))
    failures = [step for step in steps if step["status"] == "error"]
    warnings = [step for step in steps if step["status"] == "warning"]
    failing_step = failures[0] if failures else (warnings[0] if warnings else None)
    overall_status = "error" if failures else ("warning" if warnings else "ok")
    contact = support_contact(source_env)
    summary = (
        failing_step["summary"]
        if failing_step
        else "Runtime local preparado sem falhas bloqueantes."
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "summary": summary,
        "operator_message": "",
        "support_summary": "",
        "failing_step": failing_step["id"] if failing_step else None,
        "failing_step_label": failing_step["label"] if failing_step else None,
        "support_contact": contact,
        "steps": steps,
    }
    report["operator_message"] = build_operator_message(report)
    report["support_summary"] = build_support_summary(report)
    return report


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def _check_command(
    command_name: str,
    version_command: Sequence[str],
    label: str,
    *,
    required: bool,
    runner: CommandRunner,
) -> Dict[str, Any]:
    if shutil.which(command_name) is None:
        return {
            "id": command_name,
            "label": label,
            "status": "error" if required else "warning",
            "summary": f"{label} não encontrado no PATH.",
            "technical_detail": f"Comando ausente: {' '.join(version_command)}",
        }

    result = runner(version_command)
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return {
            "id": command_name,
            "label": label,
            "status": "error" if required else "warning",
            "summary": f"{label} instalado, mas falhou ao responder a versão.",
            "technical_detail": output or f"Exit code {result.returncode}",
        }

    detail = output.splitlines()[0] if output else "Versão indisponível."
    return {
        "id": command_name,
        "label": label,
        "status": "ok",
        "summary": f"{label} disponível.",
        "technical_detail": detail,
    }


def _detect_compose_command(runner: CommandRunner) -> Optional[List[str]]:
    if shutil.which("docker") is not None:
        result = runner(["docker", "compose", "version"])
        if result.returncode == 0:
            return ["docker", "compose"]
    if shutil.which("docker-compose") is not None:
        result = runner(["docker-compose", "version"])
        if result.returncode == 0:
            return ["docker-compose"]
    return None


def _check_compose(compose_cmd: Optional[List[str]], runner: CommandRunner) -> Dict[str, Any]:
    if not compose_cmd:
        return {
            "id": "docker_compose",
            "label": "Docker Compose",
            "status": "error",
            "summary": "Docker Compose não está disponível.",
            "technical_detail": "Instale `docker compose` plugin ou `docker-compose`.",
        }
    result = runner([*compose_cmd, "version"])
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return {
            "id": "docker_compose",
            "label": "Docker Compose",
            "status": "error",
            "summary": "Docker Compose respondeu com erro.",
            "technical_detail": output or f"Exit code {result.returncode}",
        }
    return {
        "id": "docker_compose",
        "label": "Docker Compose",
        "status": "ok",
        "summary": "Docker Compose disponível.",
        "technical_detail": output.splitlines()[0] if output else "Versão indisponível.",
    }


def _check_docker_daemon(runner: CommandRunner) -> Dict[str, Any]:
    if shutil.which("docker") is None:
        return {
            "id": "docker_daemon",
            "label": "Docker daemon",
            "status": "error",
            "summary": "Docker CLI ausente; não foi possível verificar o daemon.",
            "technical_detail": "Comando `docker` não encontrado.",
        }
    result = runner(["docker", "info"])
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return {
            "id": "docker_daemon",
            "label": "Docker daemon",
            "status": "error",
            "summary": "Docker daemon indisponível ou sem permissão.",
            "technical_detail": output or f"Exit code {result.returncode}",
        }
    return {
        "id": "docker_daemon",
        "label": "Docker daemon",
        "status": "ok",
        "summary": "Docker daemon acessível.",
        "technical_detail": "docker info executado com sucesso.",
    }


def _check_wsl(env: Mapping[str, str], runner: CommandRunner) -> Dict[str, Any]:
    release = platform.release().lower()
    if env.get("WSL_DISTRO_NAME") or "microsoft" in release:
        detail = env.get("WSL_DISTRO_NAME") or platform.release()
        return {
            "id": "wsl",
            "label": "WSL",
            "status": "ok",
            "summary": "Runtime detectado dentro de WSL.",
            "technical_detail": detail,
        }
    if platform.system() == "Linux":
        return {
            "id": "wsl",
            "label": "WSL",
            "status": "not_applicable",
            "summary": "WSL não se aplica a este host Linux.",
            "technical_detail": platform.platform(),
        }
    if platform.system() == "Windows":
        if shutil.which("wsl") is None and shutil.which("wsl.exe") is None:
            return {
                "id": "wsl",
                "label": "WSL",
                "status": "error",
                "summary": "WSL não encontrado neste host Windows.",
                "technical_detail": "Comando `wsl --status` indisponível.",
            }
        command = ["wsl", "--status"] if shutil.which("wsl") is not None else ["wsl.exe", "--status"]
        result = runner(command)
        output = (result.stdout or result.stderr or "").strip()
        normalized = output.lower()
        if result.returncode == 0:
            return {
                "id": "wsl",
                "label": "WSL",
                "status": "ok",
                "summary": "WSL disponível neste host Windows.",
                "technical_detail": output or "wsl --status executado com sucesso.",
            }
        if "enable the virtual machine platform" in normalized or "windows subsystem for linux has no installed distributions" in normalized:
            summary = "WSL instalado, mas ainda não está pronto para uso."
        else:
            summary = "WSL ausente ou desabilitado neste host Windows."
        return {
            "id": "wsl",
            "label": "WSL",
            "status": "error",
            "summary": summary,
            "technical_detail": output or f"Exit code {result.returncode}",
        }
    return {
        "id": "wsl",
        "label": "WSL",
        "status": "warning",
        "summary": "WSL não detectado.",
        "technical_detail": platform.platform(),
    }


def _check_path(path: Path, label: str) -> Dict[str, Any]:
    exists = path.exists()
    return {
        "id": f"path_{path.name.lower()}",
        "label": label,
        "status": "ok" if exists else "error",
        "summary": f"{label} {'disponível' if exists else 'ausente'}.",
        "technical_detail": str(path),
    }


def _check_compose_config(
    project_root: Path,
    compose_cmd: Optional[List[str]],
    runner: CommandRunner,
) -> Dict[str, Any]:
    if not compose_cmd:
        return {
            "id": "compose_config",
            "label": "Configuração do Compose",
            "status": "error",
            "summary": "Não foi possível validar o Compose sem o binário disponível.",
            "technical_detail": "Docker Compose ausente.",
        }
    result = runner([*compose_cmd, "-f", str(project_root / "docker-compose.yml"), "config", "--quiet"])
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return {
            "id": "compose_config",
            "label": "Configuração do Compose",
            "status": "error",
            "summary": "docker compose config falhou.",
            "technical_detail": output or f"Exit code {result.returncode}",
        }
    return {
        "id": "compose_config",
        "label": "Configuração do Compose",
        "status": "ok",
        "summary": "docker compose config validado.",
        "technical_detail": "Configuração sintaticamente válida.",
    }


def _check_containers_running(
    project_root: Path,
    compose_cmd: Optional[List[str]],
    runner: CommandRunner,
) -> Dict[str, Any]:
    if not compose_cmd:
        return {
            "id": "container_startup",
            "label": "Startup dos containers",
            "status": "error",
            "summary": "Não foi possível verificar containers sem Docker Compose.",
            "technical_detail": "Docker Compose ausente.",
        }
    result = runner(
        [*compose_cmd, "-f", str(project_root / "docker-compose.yml"), "ps", "--status", "running", "--services"]
    )
    output = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return {
            "id": "container_startup",
            "label": "Startup dos containers",
            "status": "warning",
            "summary": "Não foi possível listar containers em execução.",
            "technical_detail": output or f"Exit code {result.returncode}",
        }
    if not output:
        return {
            "id": "container_startup",
            "label": "Startup dos containers",
            "status": "warning",
            "summary": "Nenhum container do SOG está em execução.",
            "technical_detail": "Execute `docker compose up -d --build` ou `./scripts/start-local.sh`.",
        }
    return {
        "id": "container_startup",
        "label": "Startup dos containers",
        "status": "ok",
        "summary": "Há containers do SOG em execução.",
        "technical_detail": output.replace("\n", ", "),
    }
