import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)

    def run_cli(self, path):
        return subprocess.run(
            [sys.executable, "-m", "cli", str(path)],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
        )

    def test_accepts_one_workbook(self):
        workbook = self.folder / "plan.xlsx"
        workbook.touch()

        result = self.run_cli(workbook)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(workbook)])

    def test_selects_only_workbooks_in_folder(self):
        for name in ("b.XLSX", "a.xlsx", "~$a.xlsx", "notes.txt"):
            (self.folder / name).touch()

        result = self.run_cli(self.folder)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [str(self.folder / "a.xlsx"), str(self.folder / "b.XLSX")],
        )

    def test_reports_missing_path(self):
        result = self.run_cli(self.folder / "missing.xlsx")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Input path does not exist", result.stderr)
