---
status: accepted
---

# The Terraform skills recommend, they never force

## Context

The `terraform-authoring`, `terraform-modules`, and `terraform-review` skills encode a standards doc full of rules — naming, pinning, extraction, security floors, CI gates, local-execution etiquette. The obvious build is to make the skills *enforce* those rules: `review` fails the run on a violation, `authoring` auto-rewrites non-conforming code, the harness blocks a disallowed command. This is a solo-first, team-legible toolkit where the operator frequently knows better than the default (legacy modules, deliberate deviations, sandbox experiments), and a skill that silently blocks or rewrites stops being trusted the moment it's wrong.

## Decision

The skills **advise; they never impose.** `review` reports and the author fixes — it runs in **check-mode and never mutates files**. `authoring`/`modules` suggest. The operator can always override any rule; the standards are the *default recommendation*, not a lock. Two consequences fall out of this and are load-bearing:

- **Two audiences per rule.** Every rule is either (1) what the *artifact* should look like — advice `review` checks and `authoring` offers — or (2) how the *skill itself behaves* when it writes Terraform or runs commands (e.g. self-restricting `apply` to personal/sandbox/dev branches). The second class binds the agent's conduct, not the user's.
- **Scripted enforcement first; harness last.** Real enforcement is delegated to deterministic, scripted paths — pre-commit, `make check`, CI required-status-checks — so that "enforced" means a committed config, not the agent's memory. The AI harness only fills gaps where no scripted path exists.

## Considered options

- **Enforcing skills** (rejected): `review` fails the run, `authoring` auto-fixes. Rejected because it removes operator agency, breaks trust on false positives, and duplicates what CI/pre-commit already do deterministically.
- **Advisory skills + scripted enforcement** (chosen): the skills recommend; pre-commit/`make check`/CI enforce. Enforcement lives where it's deterministic and skippable-on-purpose; judgment lives in the skills.

## Consequences

- `review` is non-destructive and safe to run anytime, including on work-in-progress.
- A green PR means the *author* fixed it, not the pipeline — the tools stay honest.
- The one deliberate exception is a module *author* hard-locking a security floor tied to a **named compliance driver** (cited inline); even then the skill only recommends the posture, it never hard-locks a module unasked.
- Every skill's prose and defaults must be written in this advisory voice; a future reader seeing skills that never block or auto-fix should read this ADR rather than assume it's an oversight.
