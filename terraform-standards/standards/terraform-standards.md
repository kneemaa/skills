# Terraform Standards

The single canonical standards doc — the **spine** the Terraform skill family loads.
`terraform-authoring`, `terraform-modules`, and `terraform-review` all point here; a rule
lives in exactly one place in this document, and the skills reference it rather than restating it.

Consolidated by ticket *Consolidate the canonical standards doc* (T7) from three settled sections:
authoring (T4), module practices (T5), tooling/CI/local-execution (T6). The domain vocabulary these
rules use (*module, remote/local module, inline resources, extraction, values module, composition
module, leaf module, recommend-not-force, check-mode/fix-mode, break-glass flags, transient lifecycle
blocks*) is defined in [`../CONTEXT.md`](../CONTEXT.md).

## How to read this

Two structural splits govern the whole document:

- **Agnostic spine vs. provider-specific.** [Part II](#part-ii--the-provider-agnostic-spine) (§1–§6, §9–§13)
  is provider-neutral: layout, naming, interface design, extraction, tooling, CI, local execution.
  [Part III](#part-iii--provider-specific) (§7–§8, plus provider `source` addresses) is written for
  **GCP, AWS, and GitHub**, with a **seam** for the upcoming **Okta / Datadog / PagerDuty** — none of which
  have AWS/GCP-style resource tagging, so the spine never assumes tags/labels are universal.
- **Two audiences per rule** (see §0). A rule is either **artifact advice** — what a module/config should
  look like, which `review` checks against and `authoring`/`modules` offer — or **agent conduct** — how the
  skill itself behaves when it writes Terraform or runs commands (§11 and the agent-behavior anti-patterns
  in §13). Conduct rules bind the *skill*, not just the artifact.

---

## §0. Governing principles

These are map-wide: they shape how all three skills are written and how they behave, and they sit above
every numbered rule below.

- **Recommend, never force.** These skills advise; the user decides. Nothing here is a gate the skill
  imposes — `review` reports, `authoring`/`modules` suggest, and the operator can always override. Every
  rule below is the *default recommendation*, not a lock. Recorded as
  [ADR 0001](../docs/adr/0001-skills-recommend-not-force.md).
  - *Why:* solo-first, team-legible. A skill that silently blocks or rewrites erodes trust and stops being
    useful the moment the operator knows better than the default.
- **Two audiences per rule.** Each rule is either (1) **what a module/config should look like** — advice
  `review` checks and `authoring` offers — or (2) **how the skill/agent itself behaves** when it writes
  Terraform, runs commands, or asks the user to run them. The agent-behavior rules bind the skill's conduct.
- **Scripted enforcement first; harness last.** Prefer deterministic, scripted paths — pre-commit,
  `make check`, CI — to do the enforcing. The AI harness only fills gaps where **no scripted path exists**.
  If a tool can catch it, wire the tool; don't lean on the agent to remember.
- **Check-mode vs. fix-mode.** Every tool runs in one of two modes. **Check-mode never mutates files**
  (CI, `make check`, `review`); **fix-mode mutates** (`make fmt`, pre-commit, formatting code the skill
  authored). CI and `review` are always check-mode — a green PR means the *author* fixed it, not the pipeline.

---

# Part II — The provider-agnostic spine

## §1. File & directory layout

- **Split by size, not by concern-type.** Everything lives in `main.tf` until the module grows, then split
  into **topically-named files** (`labels.tf`, `nodepools.tf`, `pubsub.tf`, …). There is *no* mandated
  `security.tf` — security resources are not special-cased into their own file.
  - *Why:* consistency-by-size is predictable; special-casing security is an arbitrary rule that doesn't
    earn its keep.
- **Standard files are always present:** `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, plus the
  generated `README.md`, `.terraform-docs.yml`, and `.tflint-config.hcl`. Baseline is the
  `template-terraform-module` scaffold.
- **`examples/` is mandatory** and holds runnable `.tf`: **`default.tf`** (the required minimal/canonical
  call) + **scenario-named extras** (`with-environments.tf`, `ephemeral.tf`, `replicated.tf`, …).
  - *Why:* scenario names read better than a generic `extra.tf` / `complete.tf`.
- A full module repo also carries `.github/workflows/` (the CI gates, §10), a `Makefile` (or `justfile`)
  exposing `make check` / `make fmt` (§11), an optional rev-pinned `.pre-commit-config.yaml` (§11), and an
  optional `./modules/` directory for local modules (§6b).

## §2. Naming conventions

- The **single primary resource** of a module is labelled **`this`** (`google_storage_bucket.this`,
  `aws_s3_bucket.this`); a distinct secondary resource gets a **short descriptive label** (e.g. `logs`);
  repeated instances use `for_each` / `count` on `this`.
- Module repos are named **`terraform-<provider>-<name>`** (Registry convention): `terraform-google-vpc`,
  `terraform-github-repository`.
- **`snake_case` everywhere** — variables, outputs, locals, resource labels — enforced by tflint
  `terraform_naming_convention`.
- **On/off toggles are named `enable_<thing>`** (`enable_versioning`, not `versioning` /
  `access_logs_enabled`). Structured/non-boolean inputs stay `<thing>` or `<thing>_config`.
  - *Why:* reads as an imperative, groups toggles together, unambiguous vs. structured inputs.
- **Unit-suffixed numeric names.** Numeric inputs carry a unit suffix (`_days`, `_seconds`, `_bytes`) and
  the module converts internally where the provider wants another unit (e.g. `retention_days * 86400`).
  Generalized: **any quantity whose unit isn't obvious gets a unit-suffixed name.**

## §3. Variable interface

- **Every variable declares `type` and `description`** (tflint `terraform_typed_variables` +
  `terraform_documented_variables`). No bare `any`.
- **Minimize the required surface.** As few required inputs as possible; everything else optional with a
  sensible default. (GCP storage-bucket requires only `bucket_name`; s3 requires only `name`.)
- **Optional-when-absent uses `default = null`** (or `""` where the provider needs a string), consumed via a
  `!= null` / `!= ""` guard driving a `dynamic` block or ternary.
- **Structured inputs use `object({...})`** with `optional(field, default)` fields and a `null` default.
- **Descriptions carry the effect / why** for load-bearing defaults — substance required, **phrasing free**
  (no mandated templates; tflint enforces *presence*).
- **`validation` blocks where there's a real rule** — numeric range, format/regex, or cross-field invariant.
  **Not** for free-form strings (no manufactured validation).
- **Secrets: prefer ephemeral resources / write-only arguments** where the provider/resource supports them
  (the default module floor `>= 1.11.0` (§5) makes both ephemeral (1.10) and write-only args (1.11) available);
  **fall back to `sensitive = true`** otherwise. An output that re-exposes a sensitive input inherits
  `sensitive`.

## §4. Output interface

- **Modules must expose outputs** — a zero-output module is a defect, not a style. (The work `s3_bucket`'s
  zero outputs was a gap, not the standard.)
- **Shape: whole primary resource object + curated named scalars.** Expose the whole primary resource as one
  object (`value = google_storage_bucket.this`) *and* a few named scalars (`id`, `name`, `arn`, …) for the
  common reach-fors.
  - *Why:* the flexibility of the full object without forcing every consumer to dig into it.
- Every output has a `description` (tflint `terraform_documented_outputs`).

## §5. Provider & version pinning

*(Pinning rules are agnostic; the concrete provider `source` addresses live in [§5-P](#5-p-provider-source-addresses-provider-specific).)*

- **Every reusable module ships a `versions.tf` pinning both `required_version` and `required_providers`**
  (tflint `terraform_required_version` + `terraform_required_providers` + `terraform_unused_required_providers`).
- **Constraints are floor-only `>=`** in modules (e.g. `required_version >= 1.11.0`, `google >= 6.0.0`) —
  **not** pessimistic `~>`. Pessimistic pinning belongs at the **root**, not in a reusable module.
- **Default module floor is `required_version >= 1.11.0`** — the current baseline, which makes both
  ephemeral resources (1.10) and write-only arguments (1.11) available for the secrets guidance in §3. Raise
  the floor only when a newer feature requires it; never set it *below* 1.11.0. (This is the single default
  §3's feature-keyed floors reduce to.)
- **No `.terraform.lock.hcl` in modules.** The lock file is committed **only in root/leaf configurations**
  you actually `apply`.
  - *Why:* reusable modules stay version-flexible so the consuming root picks and locks the exact version;
    roots pin reproducibly.

## §6. Module practices — extraction, locality, structure

The heart of `terraform-modules`.

### §6a. The extraction decision — when code warrants a module

- **Rule of three gates *all* extraction.** Below three consumers, resources stay **inline** in the root
  config. Three consumers is the bar to pull them into *any* module — local or remote. Reuse is the trigger;
  a clean conceptual boundary makes the eventual module nicer but does **not** lower the count.
  - *Why:* premature extraction locks an interface before you've seen enough real call sites to know its
    shape. Two uses is a coincidence; three is a pattern.
- **A "consumer" is a distinct call site** — an existing or would-be `module` block. The rule-of-three
  count is call sites, *regardless of how many repos they span*: the **count** is what triggers extraction
  (§6a); whether those call sites **cross repo boundaries** is a separate question that chooses **remote vs.
  local** (§6b). (Example: 13 inline copies of one resource in a single root are 13 consumers — extract.)

### §6b. Local vs. remote — the second axis

Once the rule of three is met, choose locality:

- **Remote (published) is the default** for anything reused **across repos**, or that you already know will be.
- **Local (`./modules/<name>`) is optional**, for two jobs:
  1. **Incubation** — a staging ground to iterate fast before publishing, *when* the release/versioning
     overhead would slow you down. Purely the operator's choice — **going straight to remote is always valid.**
  2. **Repo-private reuse** — reused three-plus times within one repo but never shared outside it.
- **Local modules are held to the same standard as remote modules** — same typed/documented/validated
  interface, same hygiene rules, same version pinning (§5).
  - *Why:* if locality lowered the bar, local would become the lazy default, and repo-private modules that
    never graduate would drift below standard.
  - **Local-parity checklist** (self-check — observed local modules drift on exactly these): typed +
    documented variable/output interface (§3/§4); a `versions.tf` with floor-only `>=` pins (§5 — not a
    misnamed `provider.tf`, not pessimistic `~>`); a mandatory `examples/` dir (§1); outputs present (§4).
- **Graduation (local → remote):** when a local module stabilizes or a second repo needs it, publish it.
  Consumers flip `source = "./modules/x"` → the registry address `terraform-<provider>-x` **plus** a pinned
  `version`. Because local was already full-fidelity, graduation is just publishing — no rework.

### §6c. The values module (sanctioned archetype)

- **A resource-less archetype:** pure `locals` → `outputs`, no (or minimal) inputs. The single source of
  truth for org constants — label/tag taxonomy, regions, subnet plan, PAM roles.
- **One per org by default;** split only if it grows unwieldy or ownership genuinely diverges.
- **Consumed at the root only.** The root reads `terraform-<org>-global-values`, then passes constants down
  to leaf/composition modules as explicit inputs, and derives provider-level defaults (tags/labels, §7) from
  it once at the root.
  - **A reusable module reaching out to the values module itself is an anti-pattern.** Leaf modules take
    everything through their variable interface — no hidden dependency on the org's constants.
  - *Why:* keeps modules portable and testable in isolation, and keeps org-specific taxonomy from leaking
    into supposedly reusable code (critical for the Okta/Datadog/PagerDuty seam, which has no tagging concept).

### §6d. Module hygiene & composition

- **No `provider` blocks inside a reusable module.** Providers are configured at the root and passed in (via
  `configuration_aliases` where a module needs a specific aliased provider).
- **No `backend` / state config inside a reusable module.** State is a root concern only.
- **No hardcoded project IDs / regions / org constants.** They come from the values module, via the root, as
  inputs (§6c).
- **Nesting is allowed but shallow.** A **composition module** may wire together 2–3 published **leaf
  modules**; a 4-level tower is a smell. Composition modules pin the modules they call by version, like any
  consumer.

### §6e. Publishing & versioning

- **Modules are independently semver'd and published; consumers pin by version** (enforced downstream by
  tflint `terraform_module_pinned_source`, §9).
- **Mechanism is prescribed:** conventional-commit **PR titles** + **semantic-release**. Version bumps are
  inherited from the commit convention — `fix:` → patch, `feat:` → minor, `BREAKING CHANGE:` → major — not a
  separate manual decision.
- **Scope boundary:** module *distribution/versioning* is in scope as a module practice. General CI **deploy
  orchestration** (`terraform plan`/`apply` pipelines) remains **out of scope** — releasing a module
  *artifact* is not deploying *infrastructure*.

## §9. Tooling & linting

- **`tflint` ruleset is canonical and copied verbatim.** `disabled_by_default = false`, no `plugin`/`preset`
  block, the explicit rule list: `terraform_deprecated_index`, `terraform_unused_declarations`,
  `terraform_comment_syntax`, `terraform_documented_outputs`, `terraform_documented_variables`,
  `terraform_typed_variables`, `terraform_naming_convention`, `terraform_required_version`,
  `terraform_required_providers`, `terraform_unused_required_providers`, `terraform_standard_module_structure`
  — **plus** `terraform_module_pinned_source` (encodes "consumers pin by version", §6e).
- **Modules do not disable canonical rules.** The one sanctioned carve-out is the resource-less **values
  module** (§6c): no providers → **omit `required_providers` from `versions.tf` entirely and leave the
  tflint rule enabled** (cleaner than disabling the rule; the real `terraform-<org>-global-values` does
  exactly this). (`terraform-google-bootstrap` and `terraform-google-secrets` currently disable
  `required_version`/`required_providers` — **legacy drift to eliminate**, not a precedent.)
- **No severity grading.** tflint's non-zero exit fails the gate; we don't split warn vs. error.
- **Toolchain is a single pinned set, kept fresh by Dependabot** (§10). The template pins one canonical set
  (`setup-tflint@v4` + `tflint_version`, `terraform-docs/gh-actions`, `setup-terraform`, **and a pinned
  terraform version**). Version *drift* across repos is the anti-pattern (§13 #9).
- **No security scanner — settled, do not reopen.** tfsec / checkov / trivy are deliberately excluded from
  the tool stack, CI, and pre-commit (§8, §11).
- **Mechanical vs. judgment — the review boundary.** If a tool already catches it, the skill **relays the
  tool's finding; it does not re-derive it.** `terraform_unused_declarations` owns "declared and literally
  unreferenced" (vars, locals, data sources) — `review` surfaces those as *tflint* findings and never
  silently deletes them. The skill's own judgment is reserved for what the tool can't see: **unused
  *outputs*** (consumed cross-repo, tflint can't know — at most a soft "no in-repo consumer" note, never a
  delete) and **"used-but-pointless"** plumbing (a design suggestion, not a mechanical failure).

## §10. CI quality gates (NOT deploy orchestration)

- **Four parallel gates on `pull_request`, `concurrency` cancel-in-progress:**
  1. **fmt** — `terraform fmt -check -recursive`
  2. **validate** — `terraform init` + `terraform validate`
  3. **lint** — `setup-tflint` (pinned) → `tflint --config=.tflint-config.hcl`
  4. **docs** — `terraform-docs/gh-actions`, `fail-on-diff: true`, `git-push: false`
- **`pull_request` is the recommended trigger; `push: main` is the operator's option** (a green baseline on
  the default branch, at the cost of a second run).
- **Gates are toothless without repo governance — recommend it by reference.** The four checks should be
  **required status checks** with required PR + code-owner review, via the existing
  `terraform-github-repository` `github_repository_ruleset` (which also brings required signatures, linear
  history, non-fast-forward). This section *names* the requirement and points at that ruleset; it does not
  re-specify the ruleset.
- **Dependabot is mandated in the template** — terraform + github-actions ecosystems, weekly. It's the
  maintenance arm that keeps provider floors and action pins from rotting (the systemic fix for the drift in §9).
- **Out of scope, do not add:** `terraform plan` / `apply` in CI.

## §11. Local-execution etiquette (governs the skill's conduct)

- **`fmt` / `validate` / `tflint` locally before every push** — mirror CI so you never burn a red PR. The
  sanctioned way is a **`make check`** (or `just check`) target shipped in `template-terraform-module`:
  check-mode, non-mutating, identical to CI. A sibling **`make fmt`** runs fix-mode (`terraform fmt
  -recursive`, `tflint --fix`, `terraform-docs` regenerate).
  - **The author owns fix-mode.** The author runs `make fmt` (fix-mode) and then `make check` (check-mode)
    before pushing; `review` and CI are **check-mode only** and never mutate (§0). Where no `make check`
    exists, the raw-stack check-mode command for docs is **`terraform-docs --output-check`** (what
    `make check` wraps).
- **`--recursive` always** for `fmt` (a module repo has `examples/` and sometimes `./modules/` subdirs a flat
  fmt would skip).
- **`tflint --fix` in fix-mode only** — it repairs the fixable subset (e.g. `terraform_deprecated_index`); a
  convenience, never a substitute for reading the output. Never in CI or `review` (both check-mode).
- **Pre-commit is *offered*, deterministically.** The gate skills offer to wire up
  **`antonbabenko/pre-commit-terraform`** (`.pre-commit-config.yaml`, rev-pinned, committed) whose hooks map
  1:1 onto fmt/validate/tflint/terraform-docs — one toolchain behind `make check`, pre-commit, and CI. Its
  tfsec/checkov hooks stay **disabled** (§8). Chosen over raw git hooks (not auto-shared,
  `--no-verify`-skippable) and husky/npm (no Node in Terraform-only repos).
- **`apply` — the skill restricts *itself*.** The harness will not run `terraform apply` on the user's behalf
  outside **personal / sandbox / dev** branches; shared changes (staging/prod) never originate from the
  agent. **IAM is the real gate** — this is a self-imposed guard on the agent, not a security control. Local
  `plan` is always fine.
- **Surgical changes are codified, not hand-flagged.** Prefer **`import {}` / `moved {}` / `removed {}`**
  blocks so a refactor/import is reviewable code, not an out-of-band `-target`/`-replace`. `-target`/`-replace`
  are **break-glass** (diagnose, don't ship). Manual `state rm/mv` / state edits are **scripted** if truly
  unavoidable, never routine.
- **Clean up the transient blocks.** `import {}` / `moved {}` / `removed {}` are only needed for the apply
  that consumes them; after that they're dead weight. The skill **offers to remove them from prior commits**
  once they've been applied.

## §12. Documentation (terraform-docs)

- **Examples + full tables.** The generated README embeds `examples/default.tf` + scenario-named extras as
  prose, **then** the full table set: `Requirements`, `Providers`, `Modules`, `Resources`, `Inputs`,
  `Outputs`. Sections are kept even when empty (consistency over conditional templates).
  - *Why:* the Inputs/Outputs tables are the module's contract and are auto-maintained (CI `fail-on-diff`), so
    there's no upkeep cost to keeping them; the work `s3_bucket`'s examples-only README was a gap, not the
    standard.
- **`inject` mode** into `README.md` between markers, config in `.terraform-docs.yml`. (The CI `fail-on-diff`
  mechanic lives in §10.)

## §13. Anti-patterns to reject (the skill flags; the user decides)

Where a rule lives elsewhere, this list *points* at it rather than restating it.

*Module / config smells:*

1. Untyped / undocumented vars or outputs; unused declarations or unused `required_providers` — tflint-caught
   (§3, §4, §9).
2. Deprecated inline sub-blocks where the provider offers split resources (§8-P).
3. Public-by-default exposure or insecure transport allowed by default (§8).
4. Hardcoded project IDs / regions / org constants — source from the values module (§6c/§6d).
5. `provider` blocks inside a reusable module — configured at root, passed in (§6d).
6. `backend` / state config inside a reusable module (§6d).
7. Unpinned module `source` in consumers — `terraform_module_pinned_source` (§6e/§9).
8. Per-module disabling of canonical tflint rules — values-module carve-out excepted (§9).
9. Unpinned / drifting toolchain versions across repos, incl. an unpinned terraform version in CI (§9).

*Agent-behavior smells (bind the skill's conduct, §11):*

10. Routine `-target` / `-replace` — break-glass only; codify with `import`/`moved`/`removed`.
11. Ad-hoc `terraform state rm/mv` / manual state edits — script if unavoidable.
12. Leaving transient `import`/`moved`/`removed` blocks in the tree after their apply — offer cleanup.
13. Running `apply` against non-personal/sandbox/dev branches on the user's behalf.

---

# Part III — Provider-specific

Written for **GCP, AWS, and GitHub**. Each subsection is explicitly provider-scoped: the spine (Part II)
never depends on anything here. A **seam** at the end shows how **Okta / Datadog / PagerDuty** slot in without
reshaping the spine — critically, none of them have a resource-tagging concept, so §7 must never be assumed
universal.

## §5-P. Provider `source` addresses (provider-specific)

The pinning *rules* are agnostic (§5); only these `required_providers` entries change per provider:

- **GCP:** `hashicorp/google` (+ `hashicorp/google-beta` where beta features are used)
- **AWS:** `hashicorp/aws`
- **GitHub:** `integrations/github`
- **Seam:** `okta/okta`, `DataDog/datadog`, `PagerDuty/pagerduty` — same `versions.tf` shape, only this entry
  changes.

## §7. Tagging / labeling (provider-specific — NOT universal)

- **Pure pass-through is the rule.** A leaf module applies caller-supplied `tags`/`labels` verbatim. The
  **taxonomy is never the leaf module's business** — it originates in the values module (§6c) and is applied
  at the root.
- **Root owns org taxonomy and identity.** AWS `default_tags` / GCP provider default labels are set **once at
  the root**, sourced from the values module. `ManagedBy`-style module-identity tagging is a root/provider-
  default concern, **not** injected by leaf modules.
- **Carve-out — module-derived values.** A module *may* set a tag/label whose value it **derives internally**
  (e.g. a `Name` computed from module inputs). It sets values it uniquely knows; it never manufactures org
  taxonomy.
  - *Why:* provider-level default tags (AWS/GCP) make root-level tagging clean and universal, so leaves stay
    dumb — except where only the module knows the value.
- **Provider-scoped:** GCP takes `labels` (map(string), validated against GCP's label-key/value regex); AWS
  takes `tags` (map(string)).
- **Seam:** Okta / Datadog / PagerDuty have **no resource-tagging concept**. The spine must not require a
  tagging bucket, and modules for these providers simply have no §7 story.

## §8. Security defaults (provider-specific)

- **Secure-by-default, opt-in to relax.** GCP buckets: `public_access_prevention = "enforced"`, uniform
  bucket-level access, versioning on. AWS s3: Block Public Access on, TLS-deny policy, SSE configured, ACLs
  off (`BucketOwnerEnforced`).
- **Compliance floors may be un-disableable; everything else is a secure default with an override.** A module
  *may* deliberately remove the knob on a floor that maps to a **named compliance driver** (s3's
  un-disableable Block Public Access) — and when it does, it **cites the driver inline**
  (`# Pentest 2026 Astra Finding #5`, CIS, etc.). Everything else stays overridable.
  - *Why:* a hard-lock is a real, documented authorial choice, not sloppiness — but only when a compliance
    driver justifies removing operator agency. Absent that driver, secure-default-plus-override respects §0.
- **The skill recommends this posture; it never hard-locks a module unasked.** Removing a knob is the
  operator's call.
- **No security scanner** — see §9. Deliberately excluded; do not reopen.
- **Seam:** Okta / Datadog / PagerDuty have no security-defaults story here yet. Leave the seam; don't invent
  one.

## §8-P. Provider-specific note on split resources

Where a provider offers split resources over deprecated inline sub-blocks, use the split resources (AWS: the
`aws_s3_bucket_*` family, not inline blocks). Referenced by anti-pattern §13 #2.
