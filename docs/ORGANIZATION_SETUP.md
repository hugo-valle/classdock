# Organization Setup Guide

ClassDock manages GitHub Classroom assignments at the **organization level**.
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
9. Guide you through GitHub Classroom setup

### Step 3 — Complete GitHub Classroom Setup

The GitHub Classroom API does not support classroom creation.
After the wizard completes it will check whether your source org already has a classroom.
If it does, you will be offered a generated assignment checklist with one-click creation links.

**Option A — Wizard detects a source classroom (automatic checklist)**

The wizard prompts:
```
Found classroom "CS3030-Valle-S26-classroom" in source org CS3030-Valle-S26.
Generate assignment checklist from this classroom? [Y/n]:
```

Accepting generates:
- A per-assignment table with deep-link URLs to create each assignment
- A `classroom_setup.md` file in your org folder with the same checklist in Markdown

**Option B — No source classroom found (manual guidance)**

1. Go to [classroom.github.com/classrooms/new](https://classroom.github.com/classrooms/new)
2. Select your new organization (e.g., `soc-cs3030-valle-su26`)
3. Name your classroom (e.g., "CS3030 Summer 2026")
4. Create assignments using the template repos now in your org

You can also generate a checklist later:
```bash
classdock organizations classroom clone <SOURCE_CLASSROOM_ID> soc-cs3030-valle-su26
```

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

## GitHub Classroom Commands

All GitHub Classroom API operations are **read-only** — classroom and assignment
creation must be done via the web UI.  ClassDock provides inspection tools and
generates deep-link creation URLs.

### List Classrooms

```bash
# All classrooms you administer
classdock organizations classroom list

# Filtered to a specific organization
classdock organizations classroom list soc-cs3030-valle-su26
```

Output includes classroom name, linked organization, archived status, and URL.

### Browse Assignments (3-level drill-down)

```bash
# All classrooms
classdock organizations classroom assignments

# Filtered by org (fewer choices in the first menu)
classdock organizations classroom assignments soc-cs3030-valle-su26
```

The command presents three interactive menus in sequence:

```
Classrooms in 'soc-cs3030-valle-su26':

  1. CS3030-Valle-SU26-classroom  (soc-cs3030-valle-su26)

Select classroom [1-1] [1]:

Assignments in CS3030-Valle-SU26-classroom:

  1. python-basics  individual  accepted: 28
  2. midterm-project  individual  accepted: 25

Select assignment to view student repos [1-2] [1]:

       Student Repos: python-basics (CS3030-Valle-SU26-classroom)
┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃  # ┃ GitHub Username┃ Repository      ┃ Submitted ┃ Passing ┃ Commits ┃ Grade ┃
┡━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│  1 │ student-a      │ org/python-…    │           │    ✓    │      14 │ —     │
```

### Browse Grades (3-level drill-down)

```bash
classdock organizations classroom grades
classdock organizations classroom grades soc-cs3030-valle-su26
```

Same org → classroom → assignment selection flow, then displays:

```
       Grades: python-basics (CS3030-Valle-SU26-classroom)
┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃  # ┃ GitHub Username┃ Points Awarded ┃ Points Available ┃ Submitted At     ┃
┡━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│  1 │ student-a      │              8 │               10 │ 2026-04-01 ...   │
```

### Clone Classroom Structure into a New Org

```bash
# Get source classroom ID from: classdock organizations classroom list
classdock organizations classroom clone 298811 soc-cs3030-valle-fa26

# Write classroom_setup.md to a specific workspace folder
classdock organizations classroom clone 298811 soc-cs3030-valle-fa26 \
    --workspace ~/courses/soc-cs3030-valle-fa26
```

This command:
1. Fetches all assignments from the source classroom
2. Clones each starter-code repo into the target org (uses generate-from-template API)
3. Displays a checklist table with one-click assignment creation URLs
4. Writes `classroom_setup.md` to the workspace folder (or CWD)

Example output:
```
    Assignment Checklist: CS3030-S26-classroom → soc-cs3030-valle-fa26
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Assignment    ┃ Type       ┃ Deadline   ┃ Starter  ┃ Create URL               ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ python-basics │ individual │ —          │ ✓ cloned │ https://classroom.git... │
└───────────────┴────────────┴────────────┴──────────┴──────────────────────────┘
```

The Create URL opens GitHub Classroom's new-assignment form with the starter repo
pre-selected.  If the target org doesn't have a classroom yet, the URL links to the
new-classroom page instead.

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
#      clone locally, create GitHub org, fork templates, generate checklist

# 2. Verify the new org and its repos
classdock organizations verify soc-cs3030-valle-fa26

# 3. (If wizard found a source classroom) Follow the generated checklist
#    classroom_setup.md is written to ~/courses/soc-cs3030-valle-fa26/

# 4. (If no source classroom) Clone structure from a previous semester's classroom
classdock organizations classroom list                  # find the source classroom ID
classdock organizations classroom clone 298811 soc-cs3030-valle-fa26 \
    --workspace ~/courses/soc-cs3030-valle-fa26

# 5. Create the GitHub Classroom manually (API limitation)
#    → Visit classroom.github.com/classrooms/new, select the new org
#    → Use the Create URLs from the checklist to add each assignment

# ── MID-SEMESTER MONITORING ───────────────────────────────────────────

# Check student submission progress for any assignment
classdock organizations classroom assignments soc-cs3030-valle-fa26
#    → Select classroom → select assignment → student repos table

# Review grades
classdock organizations classroom grades soc-cs3030-valle-fa26
#    → Select classroom → select assignment → grades table

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

### "No classrooms found for 'ORG'"

The GitHub Classroom list endpoint returns only classrooms where you are an admin.
Make sure the organization is linked to a classroom at
[classroom.github.com](https://classroom.github.com) and that your token has the
`repo` and `read:org` scopes.

### classroom grades shows 0 points for all students

This is expected when GitHub Classroom autograding is not configured for the
assignment.  Set up autograding tests in the classroom assignment settings to
populate points data.

### `classroom clone` shows "↩ exists" for all starter repos

The repos were already cloned into the target org from a previous run.
This is idempotent — the checklist and `classroom_setup.md` are still generated
correctly using the existing repos.
