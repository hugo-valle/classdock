# Organization Setup Guide

ClassDock manages assignments at the **organization level**.
Each course has a **master template folder** containing canonical assignment repositories,
and each semester creates a new **semester org folder** linked to a GitHub organization.

---

## Local Workspace Structure

```
~/courses/                               # configurable base directory
├── CS3030/                              # master template folder (one per course)
│   ├── .classdock-master               # marker file (contains course code)
│   ├── python-basics/                   # local git clone of template repo
│   ├── midterm-project/
│   └── final-project/
└── soc-cs3030-valle-su26/              # semester org folder (one per semester)
    ├── .classdock-org                  # marker file (contains org name)
    ├── assignment.conf                  # generated ClassDock configuration
    ├── python-basics/                   # cloned from master
    ├── midterm-project/
    └── final-project/
```

---

## Naming Convention

GitHub organizations must follow this format:

```
[program-][course][-section]-[last_name]-[semester][year]
```

| Component | Rules | Example |
|-----------|-------|---------|
| program | Optional 3–4 lowercase letters | `soc`, `web`, `cybr` |
| course | Lowercase letters + 4-digit number | `cs3030`, `web1400` |
| section | Optional single digit | `2` (omit if only one section) |
| last_name | Lowercase last name | `valle`, `smith` |
| semester | `fa` / `sp` / `su` + 2-digit year | `su26`, `fa25` |

**Valid examples:**
- `soc-cs3030-valle-su26` (with program, single section)
- `cs3030-valle-su26` (no program)
- `soc-cs3550-2-smith-sp26` (program + section 2)
- `soc-web1400-valle-fa25`

---

## Quick Start

### Step 1 — Set Up Your Master Template Folder

Clone your assignment template repositories into a course folder and initialize it:

```bash
mkdir ~/courses/CS3030
cd ~/courses/CS3030

# Clone your template repos
git clone https://github.com/YOUR-ORG/python-basics
git clone https://github.com/YOUR-ORG/midterm-project

# Mark as master folder
touch .classdock-master  # or let the wizard do this automatically
```

### Step 2 — Run the Setup Wizard

```bash
cd ~/courses/CS3030
classdock organizations init
```

The wizard will:
1. Verify your GitHub token has the required scopes (`repo`, `admin:org`)
2. Detect the master template folder
3. Let you select which templates to carry forward
4. Build and validate the new organization name
5. Create the local semester org folder
6. Clone selected templates locally
7. Create the GitHub organization
8. Fork templates to the new GitHub org (marking them as GitHub templates)
9. Generate `assignment.conf` in the new org folder

### Step 3 — Verify the Organization

```bash
classdock organizations verify soc-cs3030-valle-su26
```

The template repositories are now in your new organization. Students receive
their own copies of a template; ClassDock finds them by the assignment-name
prefix.

### Step 4 — Configure and Run Assignments

```bash
cd ~/courses/soc-cs3030-valle-su26
classdock assignments setup    # configure the first assignment
classdock assignments orchestrate  # run the full workflow
```

---

## CLI Commands

### Interactive Wizard

```bash
classdock organizations init
classdock organizations init --dry-run   # preview without making changes
```

### Create Organization (Non-Interactive)

```bash
classdock organizations create \
    --login soc-cs3030-valle-su26 \
    --email instructor@weber.edu \
    --name "CS3030 Summer 2026"
```

Requires the `admin:org` scope on your GitHub token.

### Clone Templates Between Organizations

```bash
# Clone all template repos from a source org
classdock organizations clone-templates \
    --source-org CS3030-master \
    --target-org soc-cs3030-valle-su26

# Clone specific repos only
classdock organizations clone-templates \
    --source-org CS3030-master \
    --target-org soc-cs3030-valle-su26 \
    --repos python-basics \
    --repos midterm-project
```

The output is a per-repo status table:

```
     Clone: CS3030-master → soc-cs3030-valle-su26
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Repository        ┃  Status  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ project1-template │ ✓ cloned │
│ project2-template │ ↩ exists │
└───────────────────┴──────────┘

Summary: 1 cloned · 1 already existed
```

| Status | Meaning |
|--------|---------|
| `✓ cloned` | Newly created in the target org |
| `↩ exists` | Already present — skipped (idempotent) |
| `✗ failed` | Could not be cloned — check token/permissions |

### List Your GitHub Organizations

```bash
classdock organizations list
```

### Verify an Organization

```bash
classdock organizations verify soc-cs3030-valle-su26
```

Displays org details, total repo count, template repo count, and a per-repo table.

---

## GitHub Token Requirements

Your GitHub Personal Access Token must include:

| Scope | Purpose |
|-------|---------|
| `repo` | Repository access (cloning, forking) |
| `read:org` | List organization membership |
| `admin:org` | Create new organizations |

To update your token:

```bash
classdock config token <NEW_TOKEN>
```

Or set the environment variable:

```bash
export GITHUB_TOKEN=<YOUR_TOKEN>
```

---

## Typical Semester Workflow

```bash
# ── NEW SEMESTER SETUP ────────────────────────────────────────────────

# 1. Run the organization setup wizard from your master folder
cd ~/courses/CS3030
classdock organizations init
#    → Wizard: select source org, pick templates, name the new org,
#      clone locally, create GitHub org, fork templates, generate config

# 2. Verify the new org and its repos
classdock organizations verify soc-cs3030-valle-fa26

# 3. Configure and run an assignment
cd ~/courses/soc-cs3030-valle-fa26
classdock assignments setup
classdock assignments orchestrate

# ── REPEAT NEXT SEMESTER ──────────────────────────────────────────────
# Re-run classdock organizations init from the same master folder
```

---

## Troubleshooting

### "Token is missing the 'admin:org' scope"

1. Visit [github.com/settings/tokens](https://github.com/settings/tokens)
2. Select your ClassDock token
3. Enable the `admin:org` scope
4. Regenerate and update: `classdock config token <NEW_TOKEN>`

### "Organization already exists on GitHub"

The wizard will ask whether to use the existing organization.
Select "Yes" to continue setup with the existing org.

### "No git repos found in master folder"

Clone your template repositories into the master folder first:

```bash
cd ~/courses/CS3030
git clone https://github.com/YOUR-ORG/python-basics
```

### clone-templates shows `✗ failed` for a repo

- The source repo must be accessible to your token.
- Private repos require the `repo` scope.
- The target org must already exist before cloning.
- If the source repo is a GitHub template (`is_template: true`), the
  generate-from-template API is used automatically; otherwise forking is attempted.
