---
status: accepted
---

# The published site is the sole home for documentation

Documentation had drifted into several overlapping places: `docs/`, `docs-site/`, the README, and status or summary files written after each piece of work. The copies disagreed, and nothing failed when a link or nav entry broke.

User and developer documentation live in `docs-site/` and are published with MkDocs. `docs/` holds only ADRs (`docs/adr/`) and agent docs (`docs/agents/`). We do not keep status, summary or progress files in the repo; the issue, the PR and the GitHub Release notes carry that. CI runs `mkdocs build --strict`, so broken links and nav entries fail the PR.

## Considered Options

- **Keep docs in `docs/` and publish from there:** rejected. `docs/` already holds ADRs and agent docs that should not appear on the public site.
- **Rely on review to catch duplication:** rejected. A strict build catches broken links mechanically; duplication is covered by the written rule in `CLAUDE.md`.

## Consequences

- A new user or developer page needs a `mkdocs.yml` nav entry, or the strict build fails.
- Content that is neither user docs, developer docs, an ADR nor agent docs does not get a file.
