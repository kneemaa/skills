# skills

A [Claude Code](https://claude.com/claude-code) **plugin marketplace** (`kneemaa-skills`) of personal Agent Skills.

## Install

Add the marketplace, then install a plugin from it:

```
/plugin marketplace add kneemaa/skills
/plugin install terraform-standards@kneemaa-skills
```

To try changes before pushing, add the marketplace from a local checkout instead:

```
/plugin marketplace add /path/to/skills          # this repo on disk
/plugin install terraform-standards@kneemaa-skills
```

## Plugins

### `terraform-standards`

Three thin, composable Terraform skills that all load **one canonical standards doc** (the *spine*) — a rule lives in the spine once, and each skill points at it rather than restating it. The governing posture is **recommend-not-force**: the skills advise and report; you decide and can always override.

| Skill | Fires when you're… | What it does |
|-------|--------------------|--------------|
| **terraform-authoring** | writing or editing `.tf` — scaffolding a module, adding a resource, shaping a variable/output interface, pinning versions, wiring provider defaults, regenerating docs | Applies the spine's layout, naming, interface, pinning, and docs rules for GCP / AWS / GitHub. |
| **terraform-modules** | deciding whether code warrants a module | The module-design judgment: rule-of-three extraction, local-vs-remote, the values-module archetype, hygiene & composition, publishing/versioning. |
| **terraform-review** | auditing existing Terraform — a module, a PR diff, or a repo | Check-mode audit that **never mutates**: relays the tool stack (`fmt`/`validate`/`tflint`/`terraform-docs`) and adds the judgment tools can't (unused outputs, pointless plumbing). |

The **spine** (`terraform-standards/standards/terraform-standards.md`) is a **provider-agnostic core** — layout, naming, interface design, extraction, tooling, CI quality gates, local-execution etiquette — plus a **provider-specific section** for GCP, AWS, and GitHub, with a seam left for Okta / Datadog / PagerDuty. It deliberately excludes state/backend config, secrets handling, workspace strategy, CI deploy orchestration, and security scanners.

Supporting docs in the plugin: `CONTEXT.md` (the ubiquitous language) and `docs/adr/0001-skills-recommend-not-force.md` (why the skills recommend rather than enforce).

## Layout

```
.claude-plugin/marketplace.json     # marketplace manifest (lists the plugins below)
terraform-standards/                # a plugin
  .claude-plugin/plugin.json
  skills/                           # the skills Claude Code discovers
    terraform-authoring/SKILL.md
    terraform-modules/SKILL.md
    terraform-review/SKILL.md
  standards/terraform-standards.md  # the shared spine
  CONTEXT.md
  docs/adr/
```

Each skill's `SKILL.md` links the spine with a relative path (`../../standards/…`) that stays inside the plugin, so the whole plugin installs as one self-contained unit.
