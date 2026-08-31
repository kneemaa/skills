#!/usr/bin/env python3
"""Validate the plugin marketplace: manifests, skills, and relative links.

Run from anywhere: `python3 .github/scripts/validate-plugin.py`.
Exits non-zero if any check fails. Requires PyYAML.
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    sys.exit("error: PyYAML is required. Install it with: pip install pyyaml")

# Defaults to the repo this script lives in; overridable for testing against
# fixture trees.
REPO_ROOT = Path(
    os.environ.get("PLUGIN_REPO_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)*$")
# Markdown inline link: [text](target)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

failures: list[str] = []
checks = 0


def ok(msg: str) -> None:
    print(f"✓ {msg}")


def fail(msg: str) -> None:
    print(f"✗ {msg}")
    failures.append(msg)


def rel(path: Path) -> str:
    """Repo-relative path for readable output."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path):
    global checks
    checks += 1
    try:
        data = json.loads(path.read_text())
        ok(f"{rel(path)} is valid JSON")
        return data
    except FileNotFoundError:
        fail(f"{rel(path)} is missing")
    except json.JSONDecodeError as e:
        fail(f"{rel(path)} is not valid JSON: {e}")
    return None


def require(data: dict, key: str, where: str, typ=None) -> bool:
    global checks
    checks += 1
    if key not in data:
        fail(f"{where} is missing required key `{key}`")
        return False
    if typ is not None and not isinstance(data[key], typ):
        fail(f"{where} key `{key}` must be {typ.__name__}")
        return False
    return True


def validate_plugin_manifest(path: Path, expected_name: str | None) -> None:
    global checks
    data = load_json(path)
    if data is None:
        return
    where = rel(path)
    for key, typ in (("name", str), ("description", str), ("version", str)):
        require(data, key, where, typ)
    if isinstance(data.get("version"), str):
        checks += 1
        if SEMVER.match(data["version"]):
            ok(f"{where} version `{data['version']}` is semver")
        else:
            fail(f"{where} version `{data['version']}` is not valid semver")
    if expected_name is not None and data.get("name") != expected_name:
        checks += 1
        fail(
            f"{where} name `{data.get('name')}` does not match "
            f"marketplace entry `{expected_name}`"
        )


def validate_marketplace() -> list[Path]:
    """Validate marketplace.json; return the list of plugin dirs it references."""
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    data = load_json(path)
    plugin_dirs: list[Path] = []
    if data is None:
        return plugin_dirs
    where = rel(path)
    require(data, "name", where, str)
    if require(data, "owner", where, dict):
        require(data["owner"], "name", f"{where} owner", str)

    if not require(data, "plugins", where, list):
        return plugin_dirs
    global checks
    checks += 1
    if not data["plugins"]:
        fail(f"{where} `plugins` is empty")
        return plugin_dirs
    ok(f"{where} lists {len(data['plugins'])} plugin(s)")

    for i, entry in enumerate(data["plugins"]):
        label = f"{where} plugins[{i}]"
        if not isinstance(entry, dict):
            fail(f"{label} is not an object")
            continue
        has_name = require(entry, "name", label, str)
        if not require(entry, "source", label, str):
            continue
        source_dir = (REPO_ROOT / entry["source"]).resolve()
        checks += 1
        if not source_dir.is_dir():
            fail(f"{label} source `{entry['source']}` is not a directory")
            continue
        ok(f"{label} source `{entry['source']}` exists")
        plugin_dirs.append(source_dir)
        validate_plugin_manifest(
            source_dir / ".claude-plugin" / "plugin.json",
            entry["name"] if has_name else None,
        )
    return plugin_dirs


def validate_skills(plugin_dirs: list[Path]) -> None:
    global checks
    skill_files = sorted(
        f for d in plugin_dirs for f in d.glob("skills/*/SKILL.md")
    )
    if not skill_files:
        return
    for path in skill_files:
        where = rel(path)
        text = path.read_text()
        checks += 1
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not m:
            fail(f"{where} has no `---`-delimited frontmatter block")
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError as e:
            fail(f"{where} frontmatter is not valid YAML: {e}")
            continue
        if not isinstance(fm, dict):
            fail(f"{where} frontmatter is not a YAML mapping")
            continue
        ok(f"{where} frontmatter parses")
        require(fm, "name", where, str)
        require(fm, "description", where, str)
        checks += 1
        dir_name = path.parent.name
        if fm.get("name") != dir_name:
            fail(
                f"{where} name `{fm.get('name')}` "
                f"does not match directory `{dir_name}`"
            )
        else:
            ok(f"{where} name matches directory")


def validate_links() -> None:
    global checks
    md_files = sorted(
        p for p in REPO_ROOT.rglob("*.md") if ".git/" not in str(p)
    )
    broken = 0
    checked = 0
    for path in md_files:
        for target in MD_LINK.findall(path.read_text()):
            target = target.strip()
            # Skip external, anchors, absolute, and mail links.
            if target.startswith(
                ("http://", "https://", "mailto:", "#", "/")
            ):
                continue
            # Strip optional link title:  (path "title")
            target = target.split()[0]
            # Strip trailing anchor:  path.md#section
            target = target.split("#", 1)[0]
            if not target:
                continue
            checked += 1
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                broken += 1
                fail(f"{rel(path)} links to missing `{target}`")
    checks += 1
    if broken == 0:
        ok(f"{checked} relative markdown link(s) resolve")


def main() -> int:
    print(f"Validating {REPO_ROOT}\n")
    plugin_dirs = validate_marketplace()
    validate_skills(plugin_dirs)
    validate_links()

    print()
    if failures:
        print(f"FAILED: {len(failures)} problem(s) across {checks} checks.")
        return 1
    print(f"All {checks} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
