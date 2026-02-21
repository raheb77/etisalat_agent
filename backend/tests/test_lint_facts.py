import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LINTER = ROOT / "scripts" / "lint_facts.py"


def test_lint_facts_missing_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text("Statement: test", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(LINTER), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "missing frontmatter" in result.stdout


def test_lint_facts_valid_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "good.md"
    path.write_text(
        "---\n"
        "fact_id: \"fact_test\"\n"
        "title: \"Test Fact\"\n"
        "tags: ['fact']\n"
        "source: \"docs/test.md\"\n"
        "updated_at: \"2026-02-11\"\n"
        "---\n\n"
        "Statement: test\n"
        "Value(s): -\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(LINTER), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
