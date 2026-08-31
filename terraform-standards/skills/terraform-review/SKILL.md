---
name: terraform-review
description: >-
  Audit existing Terraform against the team's standards doc — a module, a PR
  diff, or a whole repo — reporting findings without editing files (check-mode).
  Use when reviewing Terraform for standards conformance, checking a module
  before opening a PR, or auditing already-merged config. Wires up
  fmt/validate/tflint/terraform-docs and adds the judgment those tools can't
  (unused outputs, pointless plumbing).
---

# terraform-review

The audit skill of the Terraform skill family. The moment: existing Terraform —
a module, a PR diff, or a whole repo — needs checking against the standard.

The **spine** at [`../../standards/terraform-standards.md`](../../standards/terraform-standards.md)
is the single source of truth for every rule. This skill points at it; it does
not restate it. Read the spine, then audit against it. The sections that shape
how `review` behaves:

- **§0 — governing principles.** `review` runs in **check-mode** and never
  mutates files; it **recommends, never forces**. A green result means the
  *author* fixed it, not the skill. ([ADR 0001](../../docs/adr/0001-skills-recommend-not-force.md).)
- **§9 — mechanical vs. judgment boundary.** The dividing line of this skill.
  If a tool catches it, `review` **relays** the tool's finding and does not
  re-derive it. Its own judgment is reserved for what tools can't see.
- **§10 — CI quality gates.** What already-merged code leans on.
- **§11 — local-execution etiquette.** How to run the tools on pre-PR work.
- **§13 — anti-patterns.** The flag list; each entry points at its home rule.

The artifact rules `review` checks a module against are §1–§8 (layout, naming,
variable/output interface, pinning, module practices, tagging, security). §13 is
the fast index into them.

## The review loop

**First, classify the artifact.** Is this a **root/leaf config** you `apply`
(has `backend`/`provider` blocks, a committed `.terraform.lock.hcl`, often no
`outputs.tf`) or a **reusable module**? Several rules *invert* by type:
`provider`/`backend` blocks, a committed lock file, and pessimistic `~>` pins are
**correct in a root** but anti-patterns in a reusable module (§5, §6d); a
zero-output root is fine, a zero-output module is a defect (§4). Classify first,
then audit only against the rules that apply — otherwise §1–§8 fire false
positives on roots.

1. **Locate the tool stack.** Prefer **`make check`** (or `just check`) — the
   check-mode target the standard ships (§11). Absent that, run the raw stack:
   `terraform fmt -check -recursive`, `terraform init && terraform validate`,
   `tflint --config=.tflint-config.hcl`, and **`terraform-docs --output-check`**
   (the docs check-mode command). Never run fix-mode (`fmt` without `-check`,
   `tflint --fix`, docs regenerate) or `apply` — check-mode never mutates (§0, §11).

2. **Pick the context.** *Pre-PR / work-in-progress* → run the stack locally so
   the author never burns a red PR (§11). *Already-merged* → lean on CI's four
   gates rather than re-running everything locally; read what CI reports (§10).
   But if CI does **not** implement §10's four gates — or runs something the
   standard bans (a security scanner like Trivy/tfsec, or `terraform plan`/`apply`
   in CI) — **report the CI divergence as a finding and fall back to the local
   stack**; don't trust non-conformant gates.

3. **Relay the mechanical layer (§9).** Surface tool findings *as the tool's
   findings*. `terraform_unused_declarations` owns declared-but-unreferenced
   vars, locals, and data sources — report those as tflint findings and
   **never silently delete them**. Do not re-derive what the tool already caught.
   If a mechanical tool **can't run** (offline, sandbox, missing config), **say so
   explicitly** and hand-check what it would have caught, labelled as a
   would-be-tool finding — never let an unrunnable tool silently drop the
   mechanical layer.

4. **Add the judgment layer (§9) — only what tools can't see.**
   - **Unused outputs.** tflint can't know about cross-repo consumers. At most a
     soft "no in-repo consumer" note — **never a delete**.
   - **Used-but-pointless plumbing.** A variable threaded through to no real
     effect, an indirection that earns nothing → a *design suggestion*, not a
     mechanical failure.

5. **Audit the artifact against the spine.** Walk §13 as the index into §1–§8:
   untyped/undocumented interface, deprecated inline sub-blocks, insecure
   defaults, hardcoded org constants, `provider`/`backend` blocks in a reusable
   module, unpinned module `source`, per-module rule disabling, drifting
   toolchain versions. For agent-conduct smells (§13 #10–#13) flag leftover
   **transient lifecycle blocks**, routine **break-glass flags**, and ad-hoc
   state edits.

6. **Report; the author decides.** Output findings — tool-relayed and
   judgment-derived, kept distinct — and stop. `review` recommends; it does not
   fix, delete, or gate (§0).
