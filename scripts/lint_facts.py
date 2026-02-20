from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import date


FACT_DIRS = [
    Path("knowledge/facts"),
    Path("backend/tests/fixtures/facts"),
]
ID_KEYS = ("fact_id", "id")
REQUIRED_KEYS = {"tags", "source"}
OPTIONAL_KEYS = {"title", "locale", "updated_at", "category"}


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def _parse_frontmatter(fm_text: str) -> dict[str, object]:
    if not fm_text.strip():
        return {}
    fm_lines = fm_text.strip().splitlines()
    data: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in fm_lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if current_list_key and line.startswith("-"):
            item = line.lstrip("-").strip().strip("'\"")
            if item:
                items = data.setdefault(current_list_key, [])
                if isinstance(items, list):
                    items.append(item)
            continue
        if ":" not in line:
            current_list_key = None
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list_key = key
        else:
            data[key] = _strip_quotes(value)
            current_list_key = None
    return data


def _strip_quotes(value: str) -> str:
    if len(value) < 2:
        return value
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1].strip()
    return value


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _infer_updated_at_from_filename(path: Path) -> str | None:
    match = re.match(r"^(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})_", path.stem)
    if not match:
        return None
    y = match.group("y")
    m = match.group("m")
    d = match.group("d")
    candidate = f"{y}-{m}-{d}"
    return candidate if _is_iso_date(candidate) else None


def _infer_title_from_body(body: str) -> str | None:
    for raw in body.splitlines():
        line = raw.strip()
        if line.lower().startswith("statement:"):
            title = line.split(":", 1)[1].strip()
            return title or None
    return None


def _normalize_tags(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip().strip("'\"") for v in value if str(v).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            if not inner:
                return []
            parts = [p.strip().strip("'\"") for p in inner.split(",")]
            return [p for p in parts if p]
        if raw:
            return [raw.strip("'\"")]
    return []


def _collect_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.glob("*.md")))
    return files


def lint_paths(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in _collect_files(paths):
        if path.name == "index.md":
            continue
        text = path.read_text(encoding="utf-8")
        fm_text, body_text = _split_frontmatter(text)
        fm = _parse_frontmatter(fm_text)
        if not fm:
            errors.append(f"{path}: missing frontmatter")
            continue
        if not any(fm.get(key) for key in ID_KEYS):
            errors.append(f"{path}: missing id (fact_id)")
        missing = [k for k in sorted(REQUIRED_KEYS) if not fm.get(k)]
        if missing:
            errors.append(f"{path}: missing keys {', '.join(missing)}")
        tags = _normalize_tags(fm.get("tags"))
        if not tags:
            errors.append(f"{path}: tags must be a non-empty list")
        title = fm.get("title")
        if not title:
            inferred_title = _infer_title_from_body(body_text)
            if not inferred_title:
                errors.append(f"{path}: missing title (frontmatter or Statement line)")
        updated_at = ""
        if isinstance(fm.get("updated_at"), str):
            updated_at = fm.get("updated_at", "").strip()
        if updated_at:
            if not _is_iso_date(updated_at):
                errors.append(f"{path}: updated_at must be ISO date (YYYY-MM-DD)")
        else:
            inferred = _infer_updated_at_from_filename(path)
            if not inferred:
                errors.append(
                    f"{path}: missing updated_at (frontmatter or YYYYMMDD_ prefix)"
                )
    return errors


def main() -> int:
    targets = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else FACT_DIRS
    errors = lint_paths(targets)
    if errors:
        print("Fact lint errors:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Facts lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
