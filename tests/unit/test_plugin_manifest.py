"""Plugin and marketplace manifests must stay consumable and honest.

The rules asserted here come from the published Claude Code plugin reference: only `name`
is required in plugin.json, marketplace.json requires `name`, `owner` and `plugins`, each
plugin entry requires `name` and `source`, and a plugin with no `skills/` directory loads
its root `SKILL.md` as a single skill. `claude plugin validate` is not available on every
machine, so these structural invariants are asserted here instead.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
SKILL = ROOT / "SKILL.md"

KEBAB = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
RESERVED_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class PluginManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = _load(PLUGIN_MANIFEST)

    def test_only_documented_fields_are_used(self) -> None:
        allowed = {
            "name", "displayName", "version", "description", "author", "homepage", "repository",
            "license", "keywords", "metadata", "engines", "dependencies", "network", "userConfig",
            "skills", "commands", "agents", "hooks", "mcpServers", "lspServers", "outputStyles",
            "workflows", "defaultEnabled", "icon", "documentationUrl", "supportUrl",
        }
        self.assertEqual(set(self.manifest) - allowed, set())

    def test_name_is_kebab_case_and_not_reserved(self) -> None:
        name = self.manifest["name"]
        self.assertRegex(name, KEBAB)
        self.assertFalse(name.startswith(RESERVED_PREFIXES), f"reserved prefix in {name}")

    def test_recommended_fields_are_present(self) -> None:
        for field in ("version", "description", "author", "homepage", "repository", "license", "keywords"):
            self.assertIn(field, self.manifest, f"missing recommended field: {field}")
        self.assertTrue(self.manifest["author"]["name"])
        self.assertEqual(self.manifest["license"], "MIT")

    def test_version_matches_project_metadata(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        declared = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE).group(1)
        self.assertEqual(self.manifest["version"], declared)

    def test_urls_are_absolute(self) -> None:
        for field in ("homepage", "repository"):
            parsed = urlparse(self.manifest[field])
            self.assertIn(parsed.scheme, {"http", "https"}, f"{field} must be an absolute URL")


class MarketplaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.marketplace = _load(MARKETPLACE)

    def test_required_top_level_fields(self) -> None:
        self.assertTrue(self.marketplace.get("name"))
        self.assertTrue(self.marketplace.get("owner", {}).get("name"))
        self.assertIsInstance(self.marketplace.get("plugins"), list)
        self.assertGreaterEqual(len(self.marketplace["plugins"]), 1)

    def test_entries_have_name_and_source(self) -> None:
        for entry in self.marketplace["plugins"]:
            self.assertTrue(entry.get("name"))
            self.assertIn("source", entry)

    def test_relative_source_resolves_and_contains_the_skill(self) -> None:
        for entry in self.marketplace["plugins"]:
            source = entry["source"]
            if isinstance(source, str):
                self.assertTrue(source.startswith("./"), "relative sources must start with ./")
                target = (ROOT / source).resolve()
                self.assertTrue(target.is_dir(), f"source does not resolve: {source}")
                self.assertTrue((target / "SKILL.md").is_file())

    def test_entries_do_not_duplicate_version(self) -> None:
        # plugin.json owns the version; a differing entry version only produces a warning.
        for entry in self.marketplace["plugins"]:
            self.assertNotIn("version", entry)


class SingleSkillLayoutTests(unittest.TestCase):
    def test_no_skills_directory_so_root_skill_is_loaded(self) -> None:
        self.assertFalse((ROOT / "skills").exists(), "single-skill layout must not add a skills/ directory")

    def test_skill_has_frontmatter_name_and_description(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---\n")[1]
        self.assertIn("name: skill-combo-bench", frontmatter)
        self.assertIn("description:", frontmatter)

    def test_skill_stays_short_and_points_at_the_repository(self) -> None:
        lines = SKILL.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 90, "SKILL.md must stay a short entry point")
        self.assertIn("https://github.com/Timevelyer/skill-combo-bench", "\n".join(lines))
        self.assertIn("docs/skill-reference.md", "\n".join(lines))

    def test_referenced_documents_exist(self) -> None:
        for relative in ("docs/skill-reference.md", "SUBMISSION.md", "README.md", "PHASE_STATUS.md"):
            self.assertTrue((ROOT / relative).is_file(), f"missing {relative}")


if __name__ == "__main__":
    unittest.main()

# FILE END: tests/unit/test_plugin_manifest.py
