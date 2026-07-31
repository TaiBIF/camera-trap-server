---
description: Push the current branch, open a PR to TaiBIF/devel, merge it, then merge TaiBIF devel into main
argument-hint: [PR title]
allowed-tools: Bash(git:*), Bash(gh:*), Read, AskUserQuestion
---

Ship the current work upstream: push → PR to `TaiBIF:devel` → merge → merge `TaiBIF:devel` into `TaiBIF:main`.

Optional PR title from the user:

$ARGUMENTS

## Repo facts

- `origin` = `moogoo78/camera-trap-server` (the user's fork). This is the only remote; there is no `upstream` remote — always target the parent repo with `gh --repo TaiBIF/camera-trap-server`.
- Parent = `TaiBIF/camera-trap-server`, default branch `devel`. The user has ADMIN there.
- `main` upstream is a long-lived release branch that sits behind `devel`.

## Steps

1. **Preflight.** Run `git status --short`, `git branch --show-current`, and `git log --oneline origin/<branch>..<branch>` (guard for a branch that has no upstream yet).
   - The repo normally carries a pile of untracked scratch files (`tmp/`, `project-281/`, CSVs, …). Ignore them — never `git add -A`.
   - If tracked files are modified or staged, stop and ask whether to commit them first. Do not commit on the user's behalf without a yes.
   - If there is nothing unpushed and no branch divergence from `TaiBIF:devel`, say so and stop — there is nothing to ship.

2. **Push.** `git push -u origin <branch>`. Never force-push.

3. **PR into `TaiBIF:devel`.** First check for an existing open PR:
   `gh pr list --repo TaiBIF/camera-trap-server --head moogoo78:<branch> --state open`
   - Reuse it if one exists. Otherwise show the user the commits that would ship and the PR title/body you intend to use, and **ask for confirmation before creating it** — this posts to an organization repo.
   - Create with:
     `gh pr create --repo TaiBIF/camera-trap-server --base devel --head moogoo78:<branch> --title "..." --body "..."`
   - Title: `$ARGUMENTS` if given, otherwise derive from the commits. Body: what changed and how it was verified. Note honestly if it was not verified against a running instance.

4. **Merge that PR.** Ask for confirmation, then `gh pr merge <number> --repo TaiBIF/camera-trap-server --merge`.
   - If the PR is not mergeable (conflicts, failing required checks), stop and report — do not attempt to resolve conflicts as part of this command.

5. **Merge `TaiBIF:devel` into `TaiBIF:main`.** This is a release step touching the upstream release branch, so **always confirm separately** — a yes in step 4 does not carry over.
   - Show what would move first: `gh api repos/TaiBIF/camera-trap-server/compare/main...devel --jq '{ahead:.ahead_by, behind:.behind_by, commits:[.commits[].commit.message|split("\n")[0]]}'`
   - If `ahead_by` is 0, report that `main` is already current and stop.
   - On confirmation, open and merge the release PR:
     `gh pr create --repo TaiBIF/camera-trap-server --base main --head devel --title "release: devel → main" --body "..."`
     then `gh pr merge <number> --repo TaiBIF/camera-trap-server --merge`.
   - If a `devel → main` PR is already open, reuse it instead of creating a second one.

6. **Report.** Give the user the PR URLs, both merge commit SHAs, and the resulting tip of `TaiBIF:main`. Mention that their local `devel` may now be behind and can be updated with `git pull`.

## Rules

- Stop at the first failure and report it. Do not retry a failed push or merge with different flags.
- Never use `--force`, `--admin`, or `--squash` unless the user explicitly asks.
- Every step that writes to `TaiBIF/*` (PR creation, both merges) needs its own explicit confirmation in chat. Do not batch them into one question.
- Do not delete branches unless the user asks.
