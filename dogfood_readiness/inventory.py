"""Small source-corpus inventory helper."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class InventoryItem:
    path: str
    kind: str


def classify_path(path: Path) -> str:
    name = path.name.lower()
    parts = {part.lower() for part in path.parts}
    suffix = path.suffix.lower()

    if ".git" in parts or "__pycache__" in parts:
        return "ignored"
    if name in {"readme.md", "contributing.md", "security.md", "license"}:
        return "project-contract"
    if ".github" in parts:
        return "ci-release"
    if "test" in name or "tests" in parts:
        return "test-evidence"
    if "docs" in parts or suffix in {".md", ".rst"}:
        return "documentation"
    if "examples" in parts:
        return "example"
    if suffix in {".py", ".rs", ".go", ".ts", ".tsx", ".js", ".swift", ".java", ".cs", ".c", ".cpp"}:
        return "implementation"
    if suffix in {".json", ".toml", ".yaml", ".yml"}:
        return "configuration"
    return "artifact"


def inventory(root: Path, max_files: int = 500) -> list[dict[str, str]]:
    """Return a bounded, deterministic inventory for reports."""

    items: list[InventoryItem] = []
    for path in sorted(root.rglob("*")):
        if len(items) >= max_files:
            break
        if not path.is_file():
            continue
        kind = classify_path(path.relative_to(root))
        if kind == "ignored":
            continue
        items.append(InventoryItem(path=str(path.relative_to(root)), kind=kind))
    return [asdict(item) for item in items]

