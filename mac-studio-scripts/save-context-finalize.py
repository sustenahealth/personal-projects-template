#!/usr/bin/env python3
"""
save-context-finalize.py — the deterministic tail of the save-context closeout.

The closeout agent does judgment (session file, INDEX, CLAUDE.md proposal).
This script does mechanics: activity log append, memory freshness bumps, and the
git commit sweep. Contract defined by:
    ~/context-system/agents/save-context-procedure.md

Subcommands
-----------
  append-activity  --tree {personal-projects,team-projects} --project FOLDER
                   --date YYYY-MM-DD --summary TEXT
  bump-memory      --date YYYY-MM-DD --files PATH [PATH ...]
  commit-sweep     --folder FOLDER --date YYYY-MM-DD [--scope PATH ...]

Hard rules
----------
* NEVER PUSH. This script commits only. Pushing is the post-commit hook's job
  (see the note in commit-sweep's report if no push hook is installed).
* Skip silently when a target is absent — a missing activity log or memory file
  is a normal condition on machines that don't carry that tree, not an error.
* Every write is atomic (temp file + os.replace) so an interrupted run cannot
  leave a half-written activity log or memory file.

Exit codes: 0 = success (including benign skips), 1 = bad input, 2 = git failure.
Python 3.9+ (no 3.10-only syntax — the Mac Studio and the laptops differ).
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile

# The three repos the closeout sweeps, in commit order.
TREES = ("personal-projects", "team-projects", "context-system")

# Cross-project activity log (vault-navigation.md). Single file, not per-tree.
ACTIVITY_REL = os.path.join("gtd", "05-context", "recent-activity.md")


# ---------------------------------------------------------------- helpers

def log(msg):
    print(msg, flush=True)


def fail(msg, code=1):
    print("error: " + msg, file=sys.stderr, flush=True)
    sys.exit(code)


def valid_date(text):
    """Argparse type: enforce YYYY-MM-DD so we never write a malformed date."""
    try:
        datetime.datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            "expected YYYY-MM-DD, got %r" % text
        )
    return text


def home(*parts):
    return os.path.join(os.path.expanduser("~"), *parts)


def git_root(path):
    """Resolve a path to its git toplevel, or None. Handles the symlinked trees
    (~/personal-projects -> ~/newco_space/personal-projects)."""
    if not os.path.isdir(path):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    return out.stdout.strip() or None


def tree_root(tree):
    """Git root for a named tree, preferring ~/<tree> then ~/newco_space/<tree>."""
    for candidate in (home(tree), home("newco_space", tree)):
        root = git_root(candidate)
        if root:
            return root
    return None


def atomic_write(path, content):
    """Write content to path atomically, preserving the original file mode."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    mode = None
    if os.path.exists(path):
        mode = os.stat(path).st_mode
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".save-context-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def run_git(root, args, dry_run=False):
    """Run a git command in root. Refuses to push, belt-and-braces."""
    if args and args[0] == "push":
        fail("commit-sweep must never push; the post-commit hook owns that", 2)
    if dry_run:
        log("      would run: git " + " ".join(args))
        return ""
    result = subprocess.run(
        ["git", "-C", root] + list(args), capture_output=True, text=True,
    )
    if result.returncode != 0:
        fail("git %s failed in %s:\n%s" % (args[0], root, result.stderr.strip()), 2)
    return result.stdout


# ---------------------------------------------------------- append-activity

def cmd_append_activity(args):
    """Append one line to the cross-project activity log.

    Format (stable, month-grouped, newest month at the bottom of its section):
        ## 2026-07
        - **2026-07-27** · team-projects/nemours-ortho-collaboration — summary
    """
    activity = None
    for base in (home("personal-projects"), home("newco_space", "personal-projects")):
        candidate = os.path.join(base, ACTIVITY_REL)
        if os.path.isfile(candidate):
            activity = candidate
            break

    if activity is None:
        log("append-activity: no recent-activity.md found — skipped "
            "(expected at ~/personal-projects/%s)" % ACTIVITY_REL)
        return

    summary = " ".join(args.summary.split())
    if len(summary) > 120:
        summary = summary[:117].rstrip() + "..."

    label = "%s/%s" % (args.tree, args.project)
    entry = "- **%s** · %s — %s" % (args.date, label, summary)

    with open(activity, "r", encoding="utf-8") as handle:
        text = handle.read()

    # Idempotent: same date + project already logged means this is a re-run.
    for line in text.splitlines():
        if line.startswith("- **%s**" % args.date) and label in line:
            log("append-activity: entry for %s on %s already present — skipped"
                % (label, args.date))
            return

    heading = "## %s" % args.date[:7]
    lines = text.splitlines()

    if heading in lines:
        # Append after the last entry belonging to this month's section.
        start = lines.index(heading)
        end = start + 1
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        insert_at = end
        while insert_at > start + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        lines.insert(insert_at, entry)
    else:
        # New month: open a section at the top of the log, under any preamble.
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith("## "):
                insert_at = index
                break
        else:
            insert_at = len(lines)
        block = [heading, "", entry, ""]
        lines[insert_at:insert_at] = block

    atomic_write(activity, "\n".join(lines).rstrip("\n") + "\n")
    log("append-activity: logged %s (%s) -> %s" % (label, args.date, activity))


# ------------------------------------------------------------- bump-memory

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)

# last_verified appears at two indent levels across the trees: flat at the top
# level (team-projects/.claude-memory) and nested under `metadata:`
# (personal-projects/.claude-memory). Capture and preserve whatever indent is
# there — rewriting it would corrupt the YAML nesting.
LAST_VERIFIED_RE = re.compile(r"^([ \t]*last_verified:[ \t]*)(.*)$", re.MULTILINE)


def cmd_bump_memory(args):
    """Set last_verified to --date in each memory file's YAML frontmatter.

    Touches only that one field; the rest of the file is preserved byte-for-byte.
    """
    bumped = skipped = 0

    for raw in args.files:
        path = os.path.abspath(os.path.expanduser(raw))

        if not os.path.isfile(path):
            log("bump-memory: %s not found — skipped" % raw)
            skipped += 1
            continue

        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()

        match = FRONTMATTER_RE.match(text)
        if not match:
            log("bump-memory: %s has no YAML frontmatter — skipped"
                % os.path.basename(path))
            skipped += 1
            continue

        frontmatter = match.group(1)
        if not LAST_VERIFIED_RE.search(frontmatter):
            log("bump-memory: %s has no last_verified field — skipped"
                % os.path.basename(path))
            skipped += 1
            continue

        current = LAST_VERIFIED_RE.search(frontmatter).group(2).strip()
        if current == args.date:
            log("bump-memory: %s already at %s — skipped"
                % (os.path.basename(path), args.date))
            skipped += 1
            continue

        new_frontmatter = LAST_VERIFIED_RE.sub(
            lambda m: m.group(1) + args.date, frontmatter, count=1
        )
        updated = text[:match.start(1)] + new_frontmatter + text[match.end(1):]

        atomic_write(path, updated)
        log("bump-memory: %s  %s -> %s"
            % (os.path.basename(path), current or "(empty)", args.date))
        bumped += 1

    log("bump-memory: %d bumped, %d skipped" % (bumped, skipped))


# ------------------------------------------------------------ commit-sweep

def cmd_commit_sweep(args):
    """Commit session work across the three trees. Never pushes.

    Default sweeps all changes in each repo (the documented behavior). Use
    --scope to restrict staging to specific paths when unrelated work in
    progress shouldn't be swept in.
    """
    message = "session: %s %s" % (args.folder, args.date)
    committed = []
    clean = []
    missing = []

    for tree in TREES:
        root = tree_root(tree)
        if root is None:
            missing.append(tree)
            log("commit-sweep: %s not present — skipped" % tree)
            continue

        log("commit-sweep: %s (%s)" % (tree, root))

        if args.scope:
            targets = [p for p in args.scope
                       if os.path.exists(os.path.join(root, p))]
            if not targets:
                log("      no --scope paths in this repo — skipped")
                clean.append(tree)
                continue
            run_git(root, ["add", "--"] + targets, args.dry_run)
        else:
            run_git(root, ["add", "-A"], args.dry_run)

        staged = run_git(root, ["diff", "--cached", "--name-only"], args.dry_run)
        names = [n for n in staged.splitlines() if n.strip()]

        if args.dry_run:
            # Preview must honour --scope, or it misrepresents what would land.
            status_cmd = ["status", "--porcelain"]
            if args.scope:
                status_cmd += ["--"] + targets
            status = run_git(root, status_cmd)
            pending = [line for line in status.splitlines() if line.strip()]
            if pending:
                log("      would commit %d change(s):" % len(pending))
                for line in pending[:25]:
                    log("        " + line)
                if len(pending) > 25:
                    log("        ... and %d more" % (len(pending) - 25))
            else:
                log("      clean — nothing to commit")
            continue

        if not names:
            log("      clean — nothing to commit")
            clean.append(tree)
            continue

        log("      staging %d file(s):" % len(names))
        for name in names[:25]:
            log("        " + name)
        if len(names) > 25:
            log("        ... and %d more" % (len(names) - 25))

        run_git(root, ["commit", "-m", message])
        sha = run_git(root, ["rev-parse", "--short", "HEAD"]).strip()
        log("      committed %s  %s" % (sha, message))
        committed.append((tree, sha, len(names)))

    log("")
    log("commit-sweep summary — message: %r" % message)
    if args.dry_run:
        log("  DRY RUN — nothing was staged or committed")
        return
    for tree, sha, count in committed:
        log("  committed  %-18s %s (%d files)" % (tree, sha, count))
    for tree in clean:
        log("  clean      %s" % tree)
    for tree in missing:
        log("  missing    %s" % tree)

    if committed:
        log("")
        log("  NOT PUSHED — by design. Verify a push hook exists, or push manually:")
        for tree, _, _ in committed:
            log("    git -C %s push" % tree_root(tree))


# ------------------------------------------------------------------- main

def build_parser():
    parser = argparse.ArgumentParser(
        prog="save-context-finalize.py",
        description="Deterministic tail for the save-context closeout "
                    "(activity log, memory bumps, commit sweep). Never pushes.",
    )
    sub = parser.add_subparsers(dest="command")

    activity = sub.add_parser(
        "append-activity", help="append one entry to the cross-project activity log")
    activity.add_argument("--tree", required=True, choices=list(TREES))
    activity.add_argument("--project", required=True, help="project folder name")
    activity.add_argument("--date", required=True, type=valid_date)
    activity.add_argument("--summary", required=True,
                          help="<=120 chars; same text as the INDEX Key Topics")
    activity.set_defaults(func=cmd_append_activity)

    memory = sub.add_parser(
        "bump-memory", help="set last_verified in memory-file frontmatter")
    memory.add_argument("--date", required=True, type=valid_date)
    memory.add_argument("--files", required=True, nargs="+",
                        help="one or more .claude-memory/*.md paths")
    memory.set_defaults(func=cmd_bump_memory)

    sweep = sub.add_parser(
        "commit-sweep", help="commit session work across the three trees (no push)")
    sweep.add_argument("--folder", required=True, help="project folder name")
    sweep.add_argument("--date", required=True, type=valid_date)
    sweep.add_argument("--scope", nargs="*", default=None, metavar="PATH",
                       help="repo-relative paths to stage instead of everything")
    sweep.add_argument("--dry-run", action="store_true",
                       help="show what would be committed, change nothing")
    sweep.set_defaults(func=cmd_commit_sweep)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
