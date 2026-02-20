#!/usr/bin/env python3
"""
Update README.md with new/removed skills by parsing SKILL.md files.

This script:
1. Extracts current skills from README.md table
2. Scans */SKILL.md files for actual skills
3. Adds new skills to table and creates detail sections
4. Removes deleted skills from table and detail sections
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"

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
            result[key.strip()] = value.strip()
    return result


def extract_requirements_from_skill(skill_path: Path) -> str:
    """Extract requirements from SKILL.md content."""
    content = skill_path.read_text()

    # Look for patterns like "Requirements:" or "## Requirements"
    req_pattern = r"\*\*Requirements[:\*\*]?\s*(.+?)(?:\n\n|\n##|\n---)"
    match = re.search(req_pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        req = match.group(1).strip()
        req = re.sub(r"\s+", " ", req).strip()
        return req

    return "See SKILL.md"


def get_skills_from_readme() -> set:
    """Extract skill names from the current README table."""
    if not README_PATH.exists():
        return set()

    content = README_PATH.read_text()
    skills = set()

    # Parse table rows - look for lines like: | [skill-name](#skill-name) | description | requirements |
    for line in content.split("\n"):
        # Match: | [skill-name](#skill-name) | description | requirements |
        match = re.match(r"\|\s*\[([a-z0-9-]+)\]\(#[a-z0-9-]+\)\s*\|", line)
        if match:
            skills.add(match.group(1))

    return skills


def get_skills_from_filesystem() -> dict:
    """Scan SKILL.md files to get skill metadata."""
    skills = {}

    for skill_path in REPO_ROOT.glob("*/SKILL.md"):
        content = skill_path.read_text()
        frontmatter = parse_frontmatter(content)

        skill_name = frontmatter.get("name", skill_path.parent.name)
        description = frontmatter.get("description", "")

        skills[skill_name] = {
            "path": skill_path,
            "description": description,
            "requirements": extract_requirements_from_skill(skill_path),
        }

    return skills


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
            # End of table is next header or horizontal rule
            if line.startswith("## ") or line.strip() == "---":
                end_line = i
                break

    return start_line, separator_line, end_line


def find_skill_details_start(content: str) -> int:
    """Find the line number where skill details sections start."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "## Skill Details":
            return i
    return -1


def find_structure_header(content: str) -> int:
    """Find the line number of the ## Structure header."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "## Structure":
            return i
    return -1


def generate_table_row(skill_name: str, description: str, requirements: str) -> str:
    """Generate a table row for a skill."""
    desc = description.strip().strip('"').replace("|", "\\|")
    req = requirements.replace("|", "\\|")
    skill_url = f"{GITHUB_REPO_URL}/tree/main/{skill_name}"
    return f"| [{skill_name}]({skill_url}) | {desc} | {req} |"


def generate_detail_section(skill_name: str, skill_path: Path) -> str:
    """Generate a detail section content (without header) for a skill."""
    content = skill_path.read_text()
    frontmatter = parse_frontmatter(content)

    description = frontmatter.get("description", "").strip().strip('"')
    requirements = extract_requirements_from_skill(skill_path)

    return f"""{description}

**Requirements:** {requirements}
**Setup:** None
**Usage:**
```bash
# See {skill_name}/SKILL.md for full documentation
```
"""


def update_readme():
    """Main function to update README.md."""
    if not README_PATH.exists():
        print(f"ERROR: {README_PATH} not found")
        sys.exit(1)

    content = README_PATH.read_text()
    lines = content.split("\n")

    # Get current state
    current_skills = get_skills_from_readme()
    filesystem_skills = get_skills_from_filesystem()

    # Find changes
    new_skills = set(filesystem_skills.keys()) - current_skills
    deleted_skills = current_skills - set(filesystem_skills.keys())

    print(f"Current skills in README: {sorted(current_skills)}")
    print(f"Skills on filesystem: {sorted(filesystem_skills.keys())}")
    print(f"New skills: {sorted(new_skills)}")
    print(f"Deleted skills: {sorted(deleted_skills)}")

    # Note: We process even if no new/deleted skills to fix formatting issues (e.g., quotes)

    # Find table boundaries
    start_line, separator_line, end_line = find_table_bounds(content)
    if start_line is None or separator_line is None or end_line is None:
        print("ERROR: Could not find skills table in README")
        sys.exit(1)

    # Find skill details start
    details_start = find_skill_details_start(content)
    if details_start == -1:
        print("ERROR: Could not find '## Skill Details' section")
        sys.exit(1)

    # Find Structure header (insert new sections before this)
    structure_line = find_structure_header(content)

    # Build new table content - preserve existing rows, add new ones
    existing_rows = []
    for i in range(separator_line + 1, end_line):
        row = lines[i]
        if row.strip().startswith("|") and not row.strip().startswith("|---"):
            # Check if this row is for a deleted skill
            match = re.match(r"\|\s*\[([a-z0-9-]+)\]\(#[a-z0-9-]+\)\s*\|", row)
            if match and match.group(1) not in deleted_skills:
                # Strip quotes from description column in existing rows
                row = re.sub(r'\|\s*"([^"]+)"\s*\|', r"| \1 |", row)
                existing_rows.append(row)
            elif not match:
                # Keep rows that don't match (might be special rows)
                existing_rows.append(row)

    # Build new table rows for new skills
    new_table_rows = []
    for skill_name in sorted(new_skills):
        skill = filesystem_skills[skill_name]
        new_table_rows.append(
            generate_table_row(skill_name, skill["description"], skill["requirements"])
        )

    # Combine existing + new rows, sorted alphabetically by skill name
    all_rows = sorted(
        existing_rows + new_table_rows,
        key=lambda row: re.search(r"\[([a-z0-9-]+)\]", row).group(1) if re.search(r"\[([a-z0-9-]+)\]", row) else row,
    )

    # Build new detail sections
    new_detail_sections = []
    for skill_name in sorted(new_skills):
        section = generate_detail_section(skill_name, filesystem_skills[skill_name]["path"])
        new_detail_sections.append("\n---\n\n" + section)

    # Rebuild the content
    new_lines = []

    # Add lines up to end of table (before separator + 1)
    new_lines.extend(lines[: separator_line + 1])

    # Add all table rows
    new_lines.extend(all_rows)

    # Add end of table marker
    new_lines.append(lines[end_line])

    # Add everything up to and including ## Skill Details
    new_lines.extend(lines[end_line + 1 : details_start + 1])

    # Rebuild all skill detail sections with correct GitHub links
    # Find where skill details end (## Structure or end of content)
    details_content = "\n".join(lines[details_start + 1 :])
    structure_match = re.search(r"\n## Structure\n", details_content)
    if structure_match:
        after_skills = details_content[structure_match.start() :]
    else:
        after_skills = ""

    # Build all skill sections fresh to ensure GitHub links are correct
    skill_sections = []
    all_skill_names = sorted(
        set(filesystem_skills.keys()) - deleted_skills
    )
    for skill_name in all_skill_names:
        section = generate_detail_section(skill_name, filesystem_skills[skill_name]["path"])
        # Strip ### header since we build it ourselves for consistent formatting
        content_only = re.sub(r"^### [a-z0-9-]+\n\n", "", section)
        skill_sections.append((skill_name, content_only.rstrip("\n")))

    # Rebuild skill details content with GitHub links on skill titles
    if skill_sections:
        rebuilt = []
        for i, (skill_name, content) in enumerate(skill_sections):
            skill_url = f"{GITHUB_REPO_URL}/tree/main/{skill_name}"
            if i == 0:
                rebuilt.append(f"### [{skill_name}]({skill_url})\n\n{content}")
            else:
                rebuilt.append(f"---\n\n### [{skill_name}]({skill_url})\n\n{content}")
        skill_details_content = "\n\n".join(rebuilt) + "\n"
    else:
        skill_details_content = ""

    details_section = skill_details_content + after_skills

    new_lines.append(details_section)

    # Write updated content
    new_content = "\n".join(new_lines)
    README_PATH.write_text(new_content)

    print(f"\nUpdated {README_PATH}")
    print(f"  - Added {len(new_skills)} new skill(s)")
    print(f"  - Removed {len(deleted_skills)} deleted skill(s)")


if __name__ == "__main__":
    update_readme()
