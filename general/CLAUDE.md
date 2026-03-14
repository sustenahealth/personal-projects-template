# General Project Folder

This is a general-purpose workspace for exploring ideas, asking questions, and prototyping before starting dedicated projects.

## Purpose
- Quick experiments and explorations
- Random questions and investigations
- Temporary work before spinning off into dedicated project folders

## Quick Start — Daily Workflow

**Open Terminal, `cd` into the project, run `claude`:**

```bash
# Personal projects
cd ~/personal-projects/general && claude

# Team projects (shared)
cd ~/team-projects/hospital-financials && claude
cd ~/team-projects/general && claude
```

**Session start** (team projects):
```bash
cd ~/team-projects/hospital-financials
git pull
claude
```
Then `/start-of-session` inside Claude.

**Session end** (team projects):
Say "save context" to Claude, then:
```bash
git add -A && git commit -m "session: <project> $(date +%Y-%m-%d)" && git push
```

**Personal projects** don't need git pull/push for daily use (single user), but do commit periodically to back up.

## Three-Repo Architecture

| Repo | Path | Purpose |
|------|------|---------|
| context-system | `~/context-system/` | Agents, skills, architecture docs |
| personal-projects | `~/personal-projects/` | Your personal project folders |
| team-projects | `~/team-projects/` | Team project folders + shared knowledge |

- `~/.claude/agents/` and `~/.claude/skills/` contain per-file symlinks created by `~/context-system/setup.sh`

## Current Focus

> New workspace — start fresh or explore something new.
