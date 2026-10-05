# ClassDock

Automation for running programming courses on plain GitHub: assignments are template repositories, students get their own copies inside an organization, and ClassDock handles discovery, secrets, collaborators, scheduling and roster tracking.

## Language

**Organization**:
The GitHub organization that owns all repositories for a course offering (e.g. `soc-cs3550-f25`).
_Avoid_: Classroom, course org

**Assignment**:
A unit of student work, identified by `Organization/Assignment name`. Its name is the prefix shared by every Student repository created for it.
_Avoid_: Classroom assignment, project, lab

**Template repository**:
The repository an Assignment is copied from for each student.
_Avoid_: Starter repo, classroom template

**Student repository**:
A student's own copy of an Assignment, living in the Organization and named with the Assignment name as prefix.
_Avoid_: Submission, classroom repo

**Roster**:
The local record of Students in an Organization and which Assignments they have accepted.
_Avoid_: Classroom roster, class list

## Retired

**GitHub Classroom**:
Decommissioned by GitHub in August 2026. ClassDock has no dependency on it; any remaining mention is legacy to remove or deprecate.
