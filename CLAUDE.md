# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

An example application demonstrating **DuckDB** with **Apache Iceberg**. The
stack is **Python** (see `.gitignore`). The repository is in an early stage —
expect to scaffold structure as features are added.

## Documentation responsibilities

- **`README.md`** holds the application's *technical documentation* (setup,
  architecture, usage, how things work). Keep it current.
- **`CLAUDE.md`** (this file) holds *working agreements and navigation* for
  Claude Code.
- **After editing anything in this repository, check whether `CLAUDE.md` or
  `README.md` needs a corresponding update — and if so, update it in the same
  change.**

## Working rules

- **Files:** read, edit, and write any file *except* `.claude/` (off-limits).
- **Git — never on `main`:** do not commit to the `main` branch. Create a
  branch for changes.
- **Git — never push:** never push to the remote. If a task requires a push,
  stop and ask the user to push it themselves.
- **TDD:** always follow Test-Driven Development for code implementation —
  write a failing test first, make it pass, then refactor.
- **Conventional Commits:** always use the
  [Conventional Commits](https://www.conventionalcommits.org/) convention for
  commit messages, merge messages, and branch names.
  - Commits/merges: `<type>(<optional scope>): <description>` — e.g.
    `feat(iceberg): add snapshot reader`, `fix: handle empty manifest`.
  - Branches: `<type>/<short-description>` — e.g. `feat/snapshot-reader`,
    `chore/setup-claude-and-gitignore`.
  - Common types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`.

## Development workflow

1. Branch off `main` before making changes.
2. Write a failing test that captures the desired behavior.
3. Implement the minimum to make it pass.
4. Refactor while keeping tests green.
5. Update `README.md` / `CLAUDE.md` if the change affects them.
6. Commit on the branch (not `main`); ask the user to push when needed.

## Commands

_To be filled in once the toolchain (test runner, dependency manager) is
established. Update this section when it is._
