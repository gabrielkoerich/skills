#!/usr/bin/env python3
"""
Update README.md, marketplace.json, and per-skill plugin.json files
by parsing SKILL.md frontmatter as the single source of truth.

This script:
1. Scans */SKILL.md files for skill metadata
2. Rebuilds the README skills table
3. Generates .claude-plugin/marketplace.json
4. Generates <skill>/.claude-plugin/plugin.json for each skill
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# GitHub repository URL (update if using a different org/user)
GITHUB_REPO_URL = "https://github.com/gabrielkoerich/skills"


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from SKILL.md content."""
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}

    frontmatter = match.group(1)
    result = {}
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def extract_requirements_from_skill(skill_path: Path) -> str:
    """Extract requirements from SKILL.md content."""
    content = skill_path.read_text()

    req_pattern = r"\*\*Requirements[:\*\*]?\s*(.+?)(?:\n\n|\n##|\n---)"
    match = re.search(req_pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        req = match.group(1).strip()
        req = re.sub(r"\s+", " ", req).strip()
        return req

    return "See SKILL.md"


def get_skills_from_filesystem() -> dict:
    """Scan SKILL.md files to get skill metadata."""
    skills = {}

    for skill_path in REPO_ROOT.glob("*/SKILL.md"):
        content = skill_path.read_text()
        frontmatter = parse_frontmatter(content)

        skill_dir = skill_path.parent
        skill_name = frontmatter.get("name", skill_dir.name)
        description = frontmatter.get("description", "")
        homepage = frontmatter.get("homepage", "")
        has_readme = (skill_dir / "README.md").exists()

        skills[skill_name] = {
            "path": skill_path,
            "dir": skill_dir.name,
            "description": description,
            "homepage": homepage,
            "requirements": extract_requirements_from_skill(skill_path),
            "has_readme": has_readme,
        }

    return skills


# ── README ─────────────────────────────────────────────────────


def find_table_bounds(content: str) -> tuple:
    """Find the line numbers for the skills table."""
    lines = content.split("\n")

    start_line = None
    separator_line = None
    end_line = None

    for i, line in enumerate(lines):
        if line.strip() == "| Skill | Description | Requirements |":
            start_line = i
        elif start_line is not None and separator_line is None:
            if line.strip().startswith("|---"):
                separator_line = i
        elif start_line is not None and separator_line is not None:
            if line.startswith("## ") or line.strip() == "---":
                end_line = i
                break

    return start_line, separator_line, end_line


def generate_table_row(skill_name: str, skill: dict) -> str:
    """Generate a table row for a skill."""
    desc = skill["description"].strip().strip('"').replace("|", "\\|")
    req = skill["requirements"].replace("|", "\\|")
    dir_name = skill["dir"]

    if skill["has_readme"]:
        skill_url = f"{GITHUB_REPO_URL}/tree/main/{dir_name}"
    else:
        skill_url = f"{GITHUB_REPO_URL}/blob/main/{dir_name}/SKILL.md"

    return f"| [{skill_name}]({skill_url}) | {desc} | {req} |"


def update_readme(filesystem_skills: dict):
    """Update README.md skills table."""
    if not README_PATH.exists():
        print(f"ERROR: {README_PATH} not found")
        sys.exit(1)

    content = README_PATH.read_text()
    lines = content.split("\n")

    start_line, separator_line, end_line = find_table_bounds(content)
    if start_line is None or separator_line is None or end_line is None:
        print("ERROR: Could not find skills table in README")
        sys.exit(1)

    table_rows = []
    for skill_name in sorted(filesystem_skills.keys()):
        table_rows.append(generate_table_row(skill_name, filesystem_skills[skill_name]))

    structure_line = None
    for i, line in enumerate(lines):
        if line.strip() == "## Structure":
            structure_line = i
            break

    new_lines = []
    new_lines.extend(lines[: separator_line + 1])
    new_lines.extend(table_rows)

    if structure_line is not None:
        new_lines.append("")
        new_lines.extend(lines[structure_line:])
    else:
        new_lines.append("")

    new_content = "\n".join(new_lines)
    README_PATH.write_text(new_content)

    print(f"Updated {README_PATH}")
    print(f"  - {len(table_rows)} skill(s) in table")


# ── Marketplace ────────────────────────────────────────────────


def update_marketplace(filesystem_skills: dict):
    """Generate .claude-plugin/marketplace.json from filesystem skills."""
    plugins = []
    for skill_name in sorted(filesystem_skills.keys()):
        skill = filesystem_skills[skill_name]
        entry = {
            "name": skill_name,
            "source": f"./{skill['dir']}",
            "description": skill["description"].strip().strip('"'),
        }
        if skill["homepage"]:
            entry["homepage"] = skill["homepage"]
        plugins.append(entry)

    marketplace = {
        "name": "skills",
        "owner": {
            "name": "Gabriel Koerich",
            "email": "gabrielmk@gmail.com",
        },
        "metadata": {
            "description": "A collection of independent, self-contained skills for AI agents.",
        },
        "plugins": plugins,
    }

    MARKETPLACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE_PATH.write_text(json.dumps(marketplace, indent=2) + "\n")

    print(f"Updated {MARKETPLACE_PATH}")
    print(f"  - {len(plugins)} plugin(s)")


def update_plugin_jsons(filesystem_skills: dict):
    """Generate .claude-plugin/plugin.json for each skill."""
    count = 0
    for skill_name in sorted(filesystem_skills.keys()):
        skill = filesystem_skills[skill_name]
        skill_dir = REPO_ROOT / skill["dir"]
        plugin_dir = skill_dir / ".claude-plugin"
        plugin_json_path = plugin_dir / "plugin.json"

        plugin = {
            "name": skill_name,
            "description": skill["description"].strip().strip('"'),
        }
        if skill["homepage"]:
            plugin["homepage"] = skill["homepage"]

        plugin_dir.mkdir(parents=True, exist_ok=True)
        plugin_json_path.write_text(json.dumps(plugin, indent=2) + "\n")
        count += 1

    print(f"Updated {count} plugin.json file(s)")


# ── Main ───────────────────────────────────────────────────────


def main():
    filesystem_skills = get_skills_from_filesystem()
    print(f"Skills on filesystem: {sorted(filesystem_skills.keys())}")
    print()

    update_readme(filesystem_skills)
    update_marketplace(filesystem_skills)
    update_plugin_jsons(filesystem_skills)


if __name__ == "__main__":
    main()
