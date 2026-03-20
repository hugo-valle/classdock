# ClassDock Command Reference

Complete reference for all `classdock` commands, subcommands, and options.

---

## Global Options

These options apply to every command:

| Option | Description |
|--------|-------------|
| `--config FILE` | Use a specific configuration file (default: `assignment.conf`) |
| `--assignment-root DIR` | Root directory containing `assignment.conf` |
| `--dry-run` | Preview actions without executing anything |
| `-v, --verbose` | Show detailed output |
| `--version` | Show the installed version |
| `--help` | Show help for any command |

---

## Shortcut Commands

Top-level shortcuts for the most common operations:

```
classdock run       Run the full assignment workflow
classdock setup     Launch the interactive assignment setup wizard
classdock fetch     Discover student repositories from GitHub Classroom
classdock status    Show assignment dashboard
classdock token     Configure your GitHub Personal Access Token
classdock completion [SHELL] [--install]  Generate or install shell tab-completion
```

---

## assignments

Assignment lifecycle management.

```
classdock assignments setup
```
Launch interactive wizard to configure a new assignment. Generates `assignment.conf`.

```
classdock assignments orchestrate
```
Execute the complete assignment workflow: sync template, discover repos, manage secrets, and optionally sync roster.

```
classdock assignments validate-config
```
Validate the `assignment.conf` file and report any issues.

```
classdock assignments help-student --repo <repo>
```
Help a specific student by updating their repository.

```
classdock assignments help-students
```
Batch version of `help-student` for multiple repositories.

```
classdock assignments check-student --repo <repo>
```
Check the status of a single student repository.

```
classdock assignments student-instructions --repo <repo>
```
Generate update instructions for a student.

```
classdock assignments check-classroom
```
Check if the classroom repository is ready for student updates.

```
classdock assignments cycle-collaborator --repo <repo>
```
Cycle collaborator permissions for a single repository.

```
classdock assignments cycle-collaborators
```
Batch version of `cycle-collaborator`.

```
classdock assignments check-repository-access --repo <repo> --user <user>
```
Check repository access status for a specific user.

```
classdock assignments push-to-classroom
```
Push template repository changes to the classroom repository.

---

## repos

Repository operations.

```
classdock repos fetch
```
Discover and save all student repositories from GitHub Classroom. Results are saved to `student-repos.txt`.

---

## secrets

Secret and token distribution.

```
classdock secrets add
```
Add or update secrets in all student repositories using the global configuration.

---

## roster

Student roster management backed by a SQLite database (`~/.config/classdock/roster.db`).

```
classdock roster init
```
Initialize the roster database (run once).

```
classdock roster import <csv-file> --org <org>
```
Import students from a CSV file. Compatible with Google Forms exports. Column names are matched case-insensitively.

```
classdock roster list [--org <org>]
```
List all students, optionally filtered by organization.

```
classdock roster add --email <email> --name <name> --org <org>
```
Add a single student to the roster.

```
classdock roster link --email <email> --github <username>
```
Link a GitHub username to an existing roster entry.

```
classdock roster sync --assignment <name> --org <org>
```
Synchronize discovered repositories (from `student-repos.txt`) with roster entries.

```
classdock roster export <output-file> [--org <org>]
```
Export roster to CSV or JSON.

```
classdock roster status [--org <org>]
```
Show roster statistics: total students, accepted assignments, unlinked entries.

---

## automation

Cron-based scheduling for automated workflow steps.

```
classdock automation cron-install
```
Install a cron job for automated workflow steps.

```
classdock automation cron-remove
```
Remove installed cron jobs.

```
classdock automation cron-status
```
Show status of all installed cron jobs.

```
classdock automation cron-logs
```
Show recent workflow log entries.

```
classdock automation cron-schedules
```
List default schedules for workflow steps.

```
classdock automation cron-sync
```
Execute the automated workflow cron job with specified steps.

---

## config

GitHub token configuration.

```
classdock config set-token
```
Update the GitHub Personal Access Token used for API operations.

```
classdock config check-token
```
Check the current token status, expiration date, and scopes.

---

## Configuration File Reference

ClassDock reads `assignment.conf` from the current directory (or a parent directory):

```bash
# Required
classroom_url="https://classroom.github.com/classrooms/<id>/assignments/<id>"
github_organization="your-github-org"
assignment_name="homework-1"

# Optional: template repository
template_repo_url="https://github.com/your-org/assignment-template"

# Optional: secrets to distribute
secrets_list="API_KEY,DATABASE_URL"

# Optional: orchestration steps
step_sync_roster=true     # Sync roster during orchestrate
```

Run `classdock setup` to generate this file interactively.
