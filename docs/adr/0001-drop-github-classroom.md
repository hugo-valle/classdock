---
status: accepted
---

# Drop GitHub Classroom; Assignments are Organization/Assignment-name on plain GitHub

GitHub decommissioned GitHub Classroom (website and APIs) in August 2026, so ClassDock no longer depends on any classroom platform. An Assignment is identified by `GITHUB_ORGANIZATION` + `ASSIGNMENT_NAME`, and Student repositories are discovered by listing Organization repos that share the Assignment-name prefix.

## Considered Options

- **Adapter for a partner platform (Classroom 50, Codio):** rejected for now. Neither is verified to expose an API ClassDock could build on, and ClassDock's value (secrets, collaborators, scheduling, Roster) needs only plain GitHub. Can return as its own issue.

## Consequences

- `CLASSROOM_URL` and `step_sync_template` are deprecated in 0.5.0 and removed in 0.6.0.
- `classroom_id` / `classroom_url` columns stay in existing `roster.db` files but are no longer read or written.
