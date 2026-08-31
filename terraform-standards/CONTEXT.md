# Terraform Skill Family

The domain language for a Claude Code skill family that encodes Nema's Terraform conventions (a standards doc plus `terraform-authoring`, `terraform-modules`, `terraform-review`). Terms here are about *how modules are designed and organized*, not Terraform's own syntax.

## Language

**Module**:
A reusable, independently-versioned unit of Terraform, one concept per module (a bucket, a GKE cluster). The default is a **remote module**.

**Remote module**:
A module published as its own repo (`terraform-<provider>-<name>`), independently semver'd and consumed by pinned version. The standard target state for anything reused across repos.
_Avoid_: package, library

**Local module**:
A module living inside a consuming repo (`./modules/<name>`), not published. Exists for two jobs: **incubation** (optional staging ground before publishing as remote) and **repo-private reuse** (reused within one repo but never shared). Held to the *same* standard as a remote module — never a less-enforced shortcut. Graduates to a remote module when it stabilizes or a second repo needs it.

**Inline resources**:
Terraform resources written directly in a root configuration, not extracted into any module. The state code stays in until extraction is warranted.

**Extraction**:
The decision to pull inline resources into a module. Gated by the **rule of three** (three consumers before extracting into *any* module, local or remote).

**Values module**:
A sanctioned resource-less archetype: pure `locals` → `outputs`, no (or minimal) inputs. The single source of truth for org constants (label taxonomy, regions, subnet plan, PAM roles). One per org by default. Anchors the "no hardcoded project IDs / regions" rule.
_Avoid_: constants file, config module

**Composition module**:
A module that wires together other (published) modules rather than declaring leaf resources directly. Allowed but kept shallow.

**Leaf module**:
A module that declares provider resources directly, calling no other modules.

**Recommend-not-force**:
The governing posture of the whole skill family: skills *advise*, they never impose. `review` reports and the author fixes; `authoring`/`modules` suggest; the operator can always override. Rules are the default recommendation, not a lock.

**Check-mode / Fix-mode**:
The two modes any tool runs in. **Check-mode** never mutates files — CI, `make check`, and `review` all report without rewriting (a green PR means the *author* fixed it, not the pipeline). **Fix-mode** mutates — `make fmt`, pre-commit, and the skill formatting code *it* authored (`terraform fmt -recursive`, `tflint --fix`).

**Break-glass flags**:
`-target` / `-replace` — acceptable to *diagnose* a problem, never to ship a normal change. A real change is a clean full plan/apply; surgical intent is codified in `import`/`moved`/`removed` blocks instead.

**Transient lifecycle blocks**:
`import {}` / `moved {}` / `removed {}` — configuration that exists only for the single apply that consumes it. Once applied it is dead weight and should be cleaned out of the tree.
