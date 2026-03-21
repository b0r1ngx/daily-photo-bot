#!/usr/bin/env python3
"""Layer dependency checker for Python. Enforces layered architecture.

Scans src/ for import violations where a lower layer imports from a higher layer.
"""
import ast
import sys
from pathlib import Path

LAYERS = {
    "types": 0,
    "config": 1,
    "repo": 2,
    "service": 3,
    "runtime": 4,
}

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src"


def get_layer(file_path: Path) -> str | None:
    """Determine which layer a file belongs to based on its path."""
    parts = file_path.relative_to(SRC_DIR).parts
    if parts:
        first_dir = parts[0]
        if first_dir in LAYERS:
            return first_dir
    return None


def get_imports(file_path: Path) -> list[str]:
    """Extract all import module paths from a Python file using AST."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def check_file(file_path: Path) -> list[str]:
    """Check a single file for layer violations. Returns list of error messages."""
    current_layer = get_layer(file_path)
    if current_layer is None:
        return []

    current_level = LAYERS[current_layer]
    imports = get_imports(file_path)
    errors = []

    for imp in imports:
        # Only check src-internal imports (start with "src.")
        if not imp.startswith("src."):
            continue

        parts = imp.split(".")
        if len(parts) < 2:
            continue

        target_module = parts[1]  # src.<layer>.xxx
        if target_module in LAYERS:
            target_level = LAYERS[target_module]
            if target_level > current_level:
                errors.append(
                    f"\n❌ ERROR [layer-violation]: {file_path}\n"
                    f"   imports '{imp}' (layer: {target_module}, level {target_level})\n"
                    f"   from layer '{current_layer}' (level {current_level})\n"
                    f"\n"
                    f"🤖 AGENT INSTRUCTION:\n"
                    f"You attempted to import an upper layer ('{target_module}') into a lower layer ('{current_layer}').\n"
                    f"This violates the Layered Architecture (see docs/architecture.md).\n"
                    f"\n"
                    f"WHY:\n"
                    f"Lower layers (like {current_layer}) must remain pure and agnostic of outer implementation details.\n"
                    f"\n"
                    f"FIX:\n"
                    f"1. Do not suppress or ignore this error.\n"
                    f"2. If you need functionality from '{target_module}', move that shared logic down to '{current_layer}' or 'types'.\n"
                    f"3. Alternatively, use Dependency Injection (pass the needed function/object as an argument).\n"
                    f"4. Refactor the import out of this file.\n"
                )
    return errors


def main() -> None:
    """Scan all Python files in src/ and check for layer violations."""
    if not SRC_DIR.exists():
        print("⚠️  No src/ directory found. Skipping layer check.")
        return

    all_errors: list[str] = []

    for py_file in sorted(SRC_DIR.rglob("*.py")):
        errors = check_file(py_file)
        all_errors.extend(errors)

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        print(f"\n❌ Layer check FAILED: {len(all_errors)} violation(s) found.", file=sys.stderr)
        sys.exit(1)
    else:
        print("✅ Python Layer Architecture Check passed.")


if __name__ == "__main__":
    main()
