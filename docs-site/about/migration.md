# Migrating from classroom-pilot

ClassDock is the renamed successor to `classroom-pilot`. This page is the only place the old name, and GitHub Classroom, are mentioned.

## Upgrade

```bash
pip uninstall classroom-pilot
pip install classdock
```

| | classroom-pilot | classdock |
|---|---|---|
| CLI command | `classroom-pilot` | `classdock` |
| Python import | `from classroom_pilot` | `from classdock` |
| Module run | `python -m classroom_pilot` | `python -m classdock` |

`assignment.conf` files keep working unchanged. Reinstall any cron jobs with `classdock automation cron-install --config path/to/assignment.conf`.

## Removed in 0.5.0

GitHub Classroom was decommissioned by GitHub in August 2026, and ClassDock no longer depends on it.

- `BashWrapper` and the `scripts_legacy/` bash scripts are removed. Use the `classdock` CLI.
- `CLASSROOM_URL` is no longer read. Set `GITHUB_ORGANIZATION` and `ASSIGNMENT_NAME` in `assignment.conf`.
- The `sync` workflow step and `STEP_SYNC_TEMPLATE` are removed. `classdock automation cron-sync` now defaults to `discover`; update any crontab entry that passes `--steps sync`.
- Cron jobs are now marked `# ClassDock Auto`. Jobs installed with the old `# GitHub Classroom Assignment Auto` marker are still listed and removable.
- Existing `roster.db` files keep their `classroom_id` / `classroom_url` columns; they are ignored.

## Versions

`classroom-pilot` ended at v3.1.2 and `classdock` starts at v0.1.0. The reset marks a rename, not a feature rollback.

Questions? [Open an issue](https://github.com/hugo-valle/classdock/issues).
