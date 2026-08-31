---
name: terraform-modules
description: Module-design judgment for Terraform. Use when deciding whether to extract inline resources into a module (rule of three), choosing a local vs. remote module or graduating one to the registry, designing or reviewing a values module, keeping a reusable module clean (no provider/backend/hardcoded constants, shallow composition), or publishing and versioning a module. Fires on the moment code might warrant a module, or an existing module is created, split, or restructured.
---

# terraform-modules

The module-design-judgment skill. It fires when someone is deciding whether code warrants a module, or is shaping one that already exists — extraction, locality, the values-module archetype, hygiene, publishing.

The rules live once in the spine: [`../../standards/terraform-standards.md`](../../standards/terraform-standards.md), §6a–§6e. The vocabulary (module, remote/local module, inline resources, extraction, values module, composition/leaf module, graduation) is defined in [`../../CONTEXT.md`](../../CONTEXT.md). This skill orients and points; it does not restate the rules — read the cited sections.

## Conduct

**Recommend, never force** (spine §0). You advise; the operator decides. Every rule below is the default recommendation, not a gate — surface the judgment call and its *why*, then let the user override.

## The decision, in order

Walk these gates in sequence when a module question comes up. Each is a spine section — open it for the rule and its rationale.

1. **Should this be a module at all? — the extraction decision (§6a).** The **rule of three** gates *all* extraction: below three consumers, resources stay **inline**. Reuse is the trigger; a clean conceptual boundary makes the eventual module nicer but never lowers the count. Two uses is a coincidence. Recommend inline until the third consumer.

2. **Local or remote? — the second axis (§6b).** Once the rule of three is met: **remote (published) is the default**. **Local (`./modules/<name>`) is optional**, for exactly two jobs — incubation, or repo-private reuse — and is held to the **same standard** as remote (typed/documented/validated interface, hygiene, version pinning). Going straight to remote is always valid. **Graduation** is a `source`-flip: `./modules/x` → the registry address `terraform-<provider>-x` plus a pinned `version`. Because local was already full-fidelity, graduation is just publishing — no rework.

3. **Is this the values module? (§6c).** The resource-less archetype — pure `locals` → `outputs`, the single source of truth for org constants. **Consumed at the root only.** The root reads it and passes constants down as explicit inputs. A **leaf module reaching for the values module itself is an anti-pattern** — leaves take everything through their variable interface. Flag it when you see it.

4. **Is the module clean? — hygiene & composition (§6d).** In a reusable module: no `provider` blocks, no `backend`/state config, no hardcoded project IDs / regions / org constants (those arrive as inputs, from the values module via the root). Nesting is allowed but **shallow** — a composition module may wire 2–3 published leaf modules; a 4-level tower is a smell. Composition modules pin what they call, like any consumer.

5. **Publishing & versioning (§6e).** Independently semver'd, consumers pin by version. Bumps are inherited from conventional-commit PR titles via semantic-release (`fix:`→patch, `feat:`→minor, `BREAKING CHANGE:`→major). Distributing a module *artifact* is in scope; deploy orchestration (plan/apply pipelines) is not.

## Reaches into the rest of the spine

A module you extract still has to satisfy the agnostic-spine rules the whole family shares — foreground these when shaping the module's actual code:

- **Interface** — variable surface (§3), outputs (§4), naming (§2), file layout & mandatory `examples/` (§1).
- **Version pinning** — floor-only `>=` in modules, no committed lock file (§5); the values module is the one sanctioned tflint carve-out (§9).
- **Provider-specific** — tagging/labeling pass-through (§7) and security defaults (§8) are written per provider (GCP/AWS/GitHub) with the Okta/Datadog/PagerDuty seam; never assume tags are universal.

For authoring a module's internals in depth, that is `terraform-authoring`'s moment; for auditing one against the spine, `terraform-review`'s.
