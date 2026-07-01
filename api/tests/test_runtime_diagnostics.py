from pathlib import Path

from sog_shared.runtime_diagnostics import run_checks


def _runner_factory(results):
    mapping = {tuple(command): value for command, value in results.items()}

    def _runner(command):
        return mapping[tuple(command)]

    return _runner


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_checks_expoe_mensagem_operador_e_detalhe_suporte(tmp_path, monkeypatch):
    project_root = tmp_path
    for rel_path in (
        ".env.api",
        ".env.agente",
        "dados",
        "dados/auth",
        "dados/screenshots",
        "dados/demonstrativos",
    ):
        (project_root / rel_path).mkdir(parents=True, exist_ok=True) if "." not in Path(rel_path).name else (project_root / rel_path).write_text("", encoding="utf-8")

    monkeypatch.setenv("SUPPORT_PHONE", "(61) 3210-4321")
    monkeypatch.setenv("SUPPORT_EMAIL", "suporte@tjdft.jus.br")
    monkeypatch.setattr("shutil.which", lambda command: f"/usr/bin/{command}")

    runner = _runner_factory(
        {
            ("docker", "compose", "version"): _Result(stdout="Docker Compose version v2.29.0"),
            ("node", "--version"): _Result(stdout="v20.11.0"),
            ("npm", "--version"): _Result(stdout="10.5.0"),
            ("docker", "--version"): _Result(stdout="Docker version 26.1.0"),
            ("docker", "info"): _Result(returncode=1, stderr="Cannot connect to the Docker daemon"),
            ("docker", "compose", "-f", str(project_root / "docker-compose.yml"), "config", "--quiet"): _Result(stdout=""),
            ("docker", "compose", "-f", str(project_root / "docker-compose.yml"), "ps", "--status", "running", "--services"): _Result(stdout="api\nfrontend"),
        }
    )

    report = run_checks(project_root=project_root, command_runner=runner)

    assert report["overall_status"] == "error"
    assert "(61) 3210-4321" in report["operator_message"]
    assert "suporte@tjdft.jus.br" in report["operator_message"]
    assert report["failing_step"] == "docker_daemon"
    assert "Docker daemon" in report["support_summary"]


def test_run_checks_preflight_nao_exige_containers_ativos(tmp_path, monkeypatch):
    project_root = tmp_path
    for rel_path in (
        ".env.api",
        ".env.agente",
        "dados",
        "dados/auth",
        "dados/screenshots",
        "dados/demonstrativos",
    ):
        (project_root / rel_path).mkdir(parents=True, exist_ok=True) if "." not in Path(rel_path).name else (project_root / rel_path).write_text("", encoding="utf-8")

    monkeypatch.setattr("shutil.which", lambda command: f"/usr/bin/{command}")

    runner = _runner_factory(
        {
            ("docker", "compose", "version"): _Result(stdout="Docker Compose version v2.29.0"),
            ("node", "--version"): _Result(stdout="v20.11.0"),
            ("npm", "--version"): _Result(stdout="10.5.0"),
            ("docker", "--version"): _Result(stdout="Docker version 26.1.0"),
            ("docker", "info"): _Result(stdout="Server Version: 26.1.0"),
            ("docker", "compose", "-f", str(project_root / "docker-compose.yml"), "config", "--quiet"): _Result(stdout=""),
        }
    )

    report = run_checks(
        project_root=project_root,
        command_runner=runner,
        include_container_runtime=False,
    )

    assert report["overall_status"] == "ok"
    assert report["failing_step"] is None
    assert all(step["id"] != "container_startup" for step in report["steps"])


def test_status_agente_expoe_runtime_diagnostic(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "rotas.agente.load_report",
        lambda: {
            "overall_status": "error",
            "operator_message": "Contate o suporte",
            "support_summary": "Etapa com falha: Docker CLI.",
            "support_contact": {
                "phone": "+1 (425) 548-4969",
                "email": "guimaraes.dpf@gmail.com",
                "is_placeholder": False,
            },
            "steps": [],
        },
    )

    resp = client.get("/api/v1/agente/status", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["runtime_diagnostic"]["overall_status"] == "error"
    assert data["runtime_diagnostic"]["operator_message"] == "Contate o suporte"
