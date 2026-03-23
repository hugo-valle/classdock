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
└── SOC-CS3030-Valle-SU26/              # semester org folder (one per semester)
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
[SUBJECT]-[COURSE][-SECTION]-[LASTNAME]-[SEMESTER][YEAR]
```

| Component | Rules | Example |
|-----------|-------|---------|
| SUBJECT | 3–4 uppercase letters | `SOC`, `WEB`, `CYBR` |
| COURSE | Uppercase letters + 4-digit number | `CS3030`, `WEB1400` |
| SECTION | Optional single digit | `2` (omit if only one section) |
| LASTNAME | Capitalized last name | `Valle`, `Smith` |
| SEMESTER | `FA` / `SP` / `SU` + 2-digit year | `SU26`, `FA25` |

**Valid examples:**
- `SOC-CS3030-Valle-SU26` (single section)
- `SOC-CS3550-2-Smith-SP26` (section 2)
- `SOC-WEB1400-Valle-FA25`

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
After the wizard completes:

1. Go to [classroom.github.com/classrooms/new](https://classroom.github.com/classrooms/new)
2. Select your new organization (e.g., `SOC-CS3030-Valle-SU26`)
3. Name your classroom (e.g., "CS3030 Summer 2026")
4. Create assignments using the template repos now in your org

### Step 4 — Configure and Run Assignments

```bash
cd ~/courses/SOC-CS3030-Valle-SU26
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
    --login SOC-CS3030-Valle-SU26 \
    --email instructor@weber.edu \
    --name "CS3030 Summer 2026"
```

Requires the `admin:org` scope on your GitHub token.

### Clone Templates Between Organizations

```bash
# Clone all template repos from a source org
classdock organizations clone-templates \
    --source-org CS3030 \
    --target-org SOC-CS3030-Valle-SU26

# Clone specific repos only
classdock organizations clone-templates \
    --source-org CS3030 \
    --target-org SOC-CS3030-Valle-SU26 \
    --repos python-basics \
    --repos midterm-project
```

### List Your GitHub Organizations

```bash
classdock organizations list
```

### Verify an Organization

```bash
classdock organizations verify SOC-CS3030-Valle-SU26
```

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
# At the start of each new semester:

# 1. Run the organization setup wizard
classdock organizations init
#    → Creates SOC-CS3030-Valle-SU26/ locally and on GitHub

# 2. Complete GitHub Classroom setup (manual)
#    → Visit classroom.github.com and create classroom

# 3. Set up individual assignments
cd ~/courses/SOC-CS3030-Valle-SU26
classdock assignments setup   # one per assignment

# 4. Run the assignment workflow
classdock assignments orchestrate

# 5. Repeat steps 3–4 for each assignment
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

### Fork fails for a specific repo

- The source repo must be accessible to your token.
- Private repos require `repo` scope.
- The target org must already exist before forking.
