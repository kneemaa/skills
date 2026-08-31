---
name: terraform-authoring
description: >-
  Writing or editing Terraform — creating or changing .tf files. Fires when you
  scaffold a module, add a resource, shape a variable or output interface, pin
  versions in versions.tf, wire provider defaults (tags/labels, security), or
  regenerate a terraform-docs README — for GCP, AWS, or GitHub. The write/edit
  skill of the Terraform standards family; loads the canonical spine for layout,
  naming, interface, pinning, and docs rules. Not for extraction/module-design
  decisions (terraform-modules) or auditing existing code (terraform-review).
---

# terraform-authoring

The write/edit skill of a three-skill Terraform family. The moment is authoring:
you are producing or changing HCL — a fresh module, a new resource, a variable,
an output, a `versions.tf`, a root config.

## The spine is the source of truth

Every rule lives once in the canonical spine:
[`../../standards/terraform-standards.md`](../../standards/terraform-standards.md).
This skill points at the sections that govern authoring; **read them there** before
writing. It never restates them — when the spine and this file seem to disagree, the
spine wins.

## Foreground — the day-to-day authoring choices

Load these sections whenever you write `.tf`:

- **§1 File & directory layout** — where a file goes, what a module repo always carries, `examples/`.
- **§2 Naming** — `this` for the primary resource, `snake_case`, `enable_<thing>` toggles, unit-suffixed numerics.
- **§3 Variable interface** — typed + documented, minimal required surface, `null`-default optionals, `object({...})` with `optional(...)`, `validation` for real rules, secrets via ephemeral / write-only args.
- **§4 Output interface** — whole primary-resource object plus curated named scalars; every output documented; no zero-output module.
- **§5 Provider & version pinning** — `versions.tf` with `>=` floors in modules, no lock file in modules.
- **§12 Documentation** — terraform-docs `inject` into `README.md`: embedded examples then full tables.

## Provider hooks

Surface the provider-specific sections for the provider you are writing — the spine
covers **GCP, AWS, and GitHub**, and leaves a **seam** for **Okta / Datadog / PagerDuty**:

- **§5-P** — provider `source` addresses for `required_providers`.
- **§7 Tagging / labeling** — GCP `labels` vs AWS `tags`; pure pass-through in leaf modules, taxonomy applied at the root. The seam providers have **no tagging concept** — never assume a tags/labels input exists.
- **§8 Security defaults** — secure-by-default with an opt-in to relax; hard-lock a knob only against a cited compliance driver. The seam providers have no §8 story yet.

Pick the section for the target provider; do not assume one provider's story holds for another.

## Conduct — recommend, never force (§0)

Offer the standard as the default; the operator decides and can always override. Suggest,
don't gate or silently rewrite.

**When you write root config, mirror module idioms** so root and module style stay aligned:
null-guarded optionals driving `dynamic` blocks, `locals` for derived values — the same
interface shapes §3 asks of a module.

## Links — the rest of the spine

Reach these when the work crosses into their moment:

- **§6 Module practices** (extraction, local-vs-remote, values module, composition) → the sibling **terraform-modules** skill owns this decision. Authoring writes what modules asks for.
- **§9–§11 Tooling, CI gates, local-execution etiquette** and **§13 anti-patterns** → **terraform-review** owns the audit. After authoring, run fix-mode (`make fmt` — `terraform fmt -recursive`, `tflint --fix`, terraform-docs regenerate) so what you wrote lands formatted and documented (§11).
