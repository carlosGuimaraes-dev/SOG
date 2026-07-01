import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "shared"))

from sog_shared.runtime_diagnostics import clear_preparation_state, load_preparation_state  # noqa: E402
from sog_shared.runtime_preparation import run_preparation_flow  # noqa: E402


class RuntimePreparationFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.tempdir.name)
        (self.project_root / "dados" / "support").mkdir(parents=True, exist_ok=True)
        self.old_cwd = Path.cwd()
        os.chdir(self.project_root)
        self.addCleanup(lambda: os.chdir(self.old_cwd))
        self.addCleanup(self.tempdir.cleanup)
        clear_preparation_state(self.project_root / "dados" / "support" / "runtime-preparation-state.json")

    def _patch_report(self, report: dict):
        return patch("sog_shared.runtime_preparation.run_checks", return_value=report)

    def test_missing_dependencies_require_authorization_and_persist_state(self) -> None:
        report = {
            "overall_status": "error",
            "summary": "Node.js ausente.",
            "operator_message": "Falha no runtime.",
            "support_summary": "Etapa com falha: Node.js.",
            "support_contact": {},
            "steps": [
                {"id": "node", "label": "Node.js", "status": "warning", "summary": "Node.js não encontrado."},
                {"id": "npm", "label": "npm", "status": "warning", "summary": "npm não encontrado."},
            ],
        }
        with self._patch_report(report):
            result = run_preparation_flow(
                project_root=self.project_root,
                env={},
                interactive=False,
            )

        self.assertEqual(result["status"], "awaiting_authorization")
        state = result["state"]
        self.assertEqual(state["phase"], "awaiting_authorization")
        self.assertEqual(state["pending_dependencies"], ["node", "npm"])

    def test_missing_npm_is_reported_as_pending_dependency(self) -> None:
        report = {
            "overall_status": "warning",
            "summary": "npm ausente.",
            "operator_message": "Falha no runtime.",
            "support_summary": "Etapa com falha: npm.",
            "support_contact": {},
            "steps": [
                {"id": "npm", "label": "npm", "status": "warning", "summary": "npm não encontrado."},
            ],
        }
        with self._patch_report(report):
            result = run_preparation_flow(
                project_root=self.project_root,
                env={},
                interactive=False,
            )

        self.assertEqual(result["status"], "awaiting_authorization")
        self.assertEqual(result["state"]["pending_dependencies"], ["npm"])

    def test_missing_docker_after_authorization_requires_manual_completion(self) -> None:
        report = {
            "overall_status": "error",
            "summary": "Docker CLI ausente.",
            "operator_message": "Falha no runtime.",
            "support_summary": "Etapa com falha: Docker CLI.",
            "support_contact": {},
            "steps": [
                {"id": "docker", "label": "Docker CLI", "status": "error", "summary": "Docker CLI não encontrado."},
            ],
        }
        with self._patch_report(report):
            result = run_preparation_flow(
                project_root=self.project_root,
                env={"SOG_RUNTIME_PREP_AUTHORIZATION": "approved"},
                interactive=False,
            )

        self.assertEqual(result["status"], "awaiting_manual_completion")
        self.assertEqual(result["guidance"][0]["id"], "docker")
        self.assertIn("docs.docker.com", result["guidance"][0]["official_source"])

    def test_wsl_authorized_flow_persists_reboot_resume_state(self) -> None:
        report = {
            "overall_status": "error",
            "summary": "WSL não detectado.",
            "operator_message": "Falha no runtime.",
            "support_summary": "Etapa com falha: WSL.",
            "support_contact": {},
            "steps": [
                {"id": "wsl", "label": "WSL", "status": "error", "summary": "WSL não detectado."},
            ],
        }
        with self._patch_report(report):
            result = run_preparation_flow(
                project_root=self.project_root,
                env={"SOG_RUNTIME_PREP_AUTHORIZATION": "approved"},
                interactive=False,
            )

        self.assertEqual(result["status"], "awaiting_reboot")
        self.assertIn("UAC", result["uac_message"])
        self.assertTrue(result["reboot_required"])
        state = load_preparation_state(self.project_root / "dados" / "support" / "runtime-preparation-state.json")
        self.assertIsNotNone(state)
        self.assertEqual(state["phase"], "awaiting_reboot")

    def test_resume_after_reboot_clears_state_when_report_is_ready(self) -> None:
        state_path = self.project_root / "dados" / "support" / "runtime-preparation-state.json"
        state_path.write_text(
            json.dumps({"phase": "awaiting_reboot", "pending_dependencies": ["wsl"]}),
            encoding="utf-8",
        )
        report = {
            "overall_status": "ok",
            "summary": "Tudo pronto.",
            "operator_message": "Runtime ok.",
            "support_summary": "Sem falhas.",
            "support_contact": {},
            "steps": [],
        }
        with self._patch_report(report):
            result = run_preparation_flow(
                project_root=self.project_root,
                env={},
                interactive=False,
            )

        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["resumed_after_reboot"])
        self.assertFalse(state_path.exists())


if __name__ == "__main__":
    unittest.main()
