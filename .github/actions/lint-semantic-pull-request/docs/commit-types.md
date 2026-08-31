**Allowed commit types and the version bump each triggers:**

| Type       | Version bump | Meaning                              |
|------------|---------------|---------------------------------------|
| `feat`     | minor         | A new feature                        |
| `fix`      | patch         | A bug fix                            |
| `perf`     | patch         | A performance improvement            |
| `proj`     | none          | Project/repo-level change            |
| `docs`     | none          | Documentation only                   |
| `style`    | none          | Formatting, no code change           |
| `refactor` | none          | Code change with no behavior change  |
| `test`     | none          | Adding or fixing tests               |
| `build`    | none          | Build system or dependency change    |
| `ci`       | none          | CI configuration change              |
| `chore`    | none          | Maintenance, no production code change |
| `revert`   | patch         | Reverts a previous commit            |
| `release`  | none          | Release-only commit                  |

A `!` after the type (e.g. `feat!:`) or a `BREAKING CHANGE:` footer always
triggers a major bump, regardless of type.
