import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class StartLocalScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        (self.repo_root / "scripts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / ".env.example").write_text("JWT_SECRET_KEY=test\n", encoding="utf-8")
        self._copy_script("start-local.sh")
        self._copy_script("prepare-runtime.sh")

        fakebin = self.repo_root / "fakebin"
        fakebin.mkdir()
        self._write_executable(
            fakebin / "python3",
            textwrap.dedent(
                """\
                #!/usr/bin/python3
                import json
                import sys
                from pathlib import Path

                script_path = Path(sys.argv[1]).name
                root = Path(sys.argv[1]).resolve().parent.parent
                support_dir = root / "dados" / "support"
                support_dir.mkdir(parents=True, exist_ok=True)

                if script_path == "prepare-internal-runtime.py":
                    print("prepare ok")
                    raise SystemExit(0)

                if script_path == "runtime_diagnostics.py":
                    expected_paths = [
                        root / ".env.api",
                        root / ".env.agente",
                        root / "dados",
                        root / "dados" / "auth",
                        root / "dados" / "screenshots",
                        root / "dados" / "demonstrativos",
                    ]
                    missing = [str(path.relative_to(root)) for path in expected_paths if not path.exists()]
                    if "--write-report" in sys.argv:
                        (support_dir / "runtime-diagnostic.json").write_text(
                            json.dumps({"overall_status": "ok"}) + "\\n",
                            encoding="utf-8",
                        )
                    if missing:
                        print("missing bootstrap paths: " + ", ".join(missing), file=sys.stderr)
                        raise SystemExit(1)
                    print("diagnostics ok")
                    raise SystemExit(0)

                print(f"unexpected python call: {sys.argv}", file=sys.stderr)
                raise SystemExit(1)
                """
            ),
        )
        self._write_executable(
            fakebin / "docker",
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                if [[ "$1" == "compose" && "$4" == "up" ]]; then
                  echo "docker compose up ok"
                  exit 0
                fi
                echo "unexpected docker call: $*" >&2
                exit 1
                """
            ),
        )
        self.env = os.environ.copy()
        self.env["PATH"] = f"{fakebin}:{self.env['PATH']}"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _copy_script(self, name: str) -> None:
        source = ROOT / "scripts" / name
        target = self.repo_root / "scripts" / name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        target.chmod(target.stat().st_mode | stat.S_IXUSR)

    def _write_executable(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def test_start_local_bootstraps_runtime_before_preflight(self) -> None:
        result = subprocess.run(
            ["bash", str(self.repo_root / "scripts" / "start-local.sh")],
            cwd=self.repo_root,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((self.repo_root / ".env.api").exists())
        self.assertTrue((self.repo_root / ".env.agente").exists())
        self.assertTrue((self.repo_root / "dados" / "auth").exists())
        self.assertIn("docker compose up ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
