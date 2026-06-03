# Git Workflow for Enterprise RAG - 4-Hour Sprint

You are working on **Backend (Person 2)**, **Infra (Person 5)**, and **Evaluation (Person 5)**.

## Your Branches

Your feature branches are already created on `dev`:

```
feat/p2-api-endpoints          # FastAPI route implementations
feat/p2-auth-rbac              # Authentication and RBAC middleware
feat/p5-infra-docker           # Docker Compose and infrastructure
feat/p5-seed-documents         # Demo document preparation
feat/p5-evaluation-experiments # Experiment runner and metrics
```

## Branch Strategy Overview

```
main (protected)
  ↑
  └─ dev (integration branch)
      ├── feat/p2-api-endpoints
      ├── feat/p2-auth-rbac
      ├── feat/p5-infra-docker
      ├── feat/p5-seed-documents
      └── feat/p5-evaluation-experiments
```

**Key Rule**: All work starts from `dev`, never from `main`. At T+210m, Person 5 cuts `main` from `dev` for final demo.

## Commit Message Format

Use conventional commits for clarity:

```
feat(scope): description
fix(scope): description
chore(scope): description
```

**Scope options for your work**: `backend`, `infra`, `evaluation`

**Examples**:
```
feat(backend): implement POST /api/v1/chat endpoint with RBAC filter
feat(infra): setup docker-compose with health checks
fix(backend): correct JWT token extraction in middleware
feat(evaluation): add MRR metric calculation
chore(infra): update postgres schema for feedback table
```

## Daily Workflow

### Morning: Start Your Day

```bash
# Update local dev branch
git checkout dev
git pull origin dev

# Start work on your feature
git checkout feat/p2-api-endpoints  # (or your assigned branch)

# Sync with latest dev changes
git rebase origin/dev
```

### During Development: Make Commits

```bash
# Make changes to files
vim backend/app/routers/chat.py

# Stage your changes
git add backend/app/routers/chat.py

# Commit with clear message
git commit -m "feat(backend): implement chat endpoint with source attribution"

# Push regularly to avoid losing work
git push origin feat/p2-api-endpoints
```

### Before Merging: Keep Branch Fresh

```bash
# Fetch latest changes
git fetch origin

# Rebase on latest dev to avoid merge conflicts
git rebase origin/dev

# Force push only your branch (not main/dev)
git push origin feat/p2-api-endpoints --force-with-lease
```

### Merging to dev: Create a PR

When your work is done (or at checkpoint time):

```bash
# Ensure branch is clean
git status
# (should show no uncommitted changes)

# Push your branch
git push origin feat/p2-api-endpoints

# Create PR on GitHub/GitLab
# Title: "feat(backend): implement auth endpoints"
# Description: What changed and why
# Request review from a teammate
```

After review approval:

```bash
# Update your branch once more
git fetch origin
git rebase origin/dev

# Merge to dev (squash-merge to keep history clean)
git checkout dev
git pull origin dev
git merge --squash feat/p2-api-endpoints
git commit -m "feat(backend): implement auth endpoints"
git push origin dev
```

## Critical Timeline Checkpoints

### T+0: Project Kickoff
- ✅ All branches created
- ✅ Assignments clear
- Action: `git checkout feat/p2-api-endpoints` and start working

### T+30m: Foundations Checkpoint
**Deliverables**:
- [ ] Docker Compose running locally (`docker-compose up -d`)
- [ ] PostgreSQL, Qdrant, Redis all healthy
- [ ] `schemas.py` merged to dev (API contracts frozen)
- [ ] All feature branches pushed to origin

**Git action**:
```bash
git checkout dev
git merge --no-ff feat/p2-api-endpoints  # Backend skeleton
git merge --no-ff feat/p5-infra-docker   # Docker working
git commit -m "chore: checkpoint 1 - foundations ready"
git push origin dev
```

### T+90m: Component Integration Checkpoint
**Deliverables**:
- [ ] All components working in isolation
- [ ] Backend routes returning proper responses (even if data comes from stubs)
- [ ] Ingestion pipeline parses at least 1 document
- [ ] Retrieval returns mock results
- [ ] Tests passing

**Git action**:
```bash
git checkout dev
git pull origin dev
git merge --squash feat/p2-api-endpoints
git merge --squash feat/p5-seed-documents
git commit -m "feat: checkpoint 2 - all components isolated"
git push origin dev
```

### T+150m: Full Integration Checkpoint
**Deliverables**:
- [ ] Chat flow end-to-end working
- [ ] Both chunking strategies in Qdrant
- [ ] Vector vs hybrid comparison data captured
- [ ] RBAC enforcement verified

**Git action**:
```bash
git checkout dev
git pull origin dev
git merge --squash feat/p5-evaluation-experiments
git commit -m "feat: checkpoint 3 - full integration"
git push origin dev
```

### T+210m: Final Demo
**Deliverables**:
- [ ] All code merged to dev
- [ ] No broken tests
- [ ] Demo script ready

**Git action** (by Person 5):
```bash
git checkout main
git pull origin main
git merge --no-ff dev --no-edit
git tag -a v1.0-demo -m "Enterprise RAG Demo - Final"
git push origin main
git push origin v1.0-demo
```

## Handling Issues During Development

### You made a mistake in a commit

**Option A: Undo and redo** (for unpushed commits)
```bash
git reset --soft HEAD~1  # Keep changes, undo commit
git add .
git commit -m "feat(backend): correct implementation"
```

**Option B: Fix with a new commit** (for pushed commits)
```bash
# Make your fix
git add .
git commit -m "fix(backend): correct jwt validation logic"
# Push normally - the fix commits tell the story
git push origin feat/p2-api-endpoints
```

### You're out of sync with dev

```bash
git fetch origin
git rebase origin/dev

# If conflicts arise:
# 1. Resolve conflicts in your files
# 2. Stage resolved files: git add .
# 3. Continue rebase: git rebase --continue
# 4. Force-push your branch: git push origin feat/p2-api-endpoints --force-with-lease
```

### You accidentally committed to main

```bash
git branch feat/save-my-work
git reset --hard origin/main
git checkout feat/save-my-work
# Now your work is safe on the new branch
```

### You want to see what you've changed compared to dev

```bash
git diff origin/dev...HEAD
# or
git diff origin/dev
# or show commits only in your branch
git log origin/dev..HEAD --oneline
```

## Useful Git Commands

```bash
# See all branches and which one you're on
git branch -a

# See commit history with all branches as a tree
git log --oneline --all --graph --decorate

# See status of current branch
git status

# See what you changed
git diff

# See what you changed (staged only)
git diff --staged

# See recent commits
git log -10 --oneline

# See commits only on your branch
git log origin/dev..HEAD --oneline

# Clean up merged local branches
git branch -d feat/completed-feature
```

## Team Communication via Git

When you need to announce something to the team:

1. **Schema change needed?** 
   - Post message to Slack/Discord
   - Wait for team approval
   - Update `backend/app/models/schemas.py`
   - Push immediately
   
2. **Major infrastructure change?**
   - Discuss with Person 5 first
   - Update docker-compose.yml
   - Push to feat/p5-infra-docker
   
3. **Database schema change?**
   - Update infra/db/init.sql
   - Test locally: `docker-compose down -v && docker-compose up`
   - Announce to team

## Merge Conflict Prevention

The folder structure prevents most conflicts:

```
backend/
  ├── routers/auth.py          ← You own
  ├── routers/chat.py          ← You own
  ├── models/schemas.py        ← SHARED - frozen at T+30m
  └── app/main.py              ← You own

infra/
  ├── db/init.sql              ← You own
  └── qdrant/config.yaml       ← You own

evaluation/
  ├── metrics.py               ← You own
  └── experiment_runner.py     ← You own
```

**Only conflict risk**: `schemas.py` - it's FROZEN at T+30m. No changes after that without team announcement.

## Emergency Commands (Use with Care)

```bash
# Undo the last commit (keep the changes)
git reset --soft HEAD~1

# Undo the last commit (discard all changes)
git reset --hard HEAD~1

# Go back to what's on origin
git reset --hard origin/feat/p2-api-endpoints

# See what you're about to lose
git diff origin/feat/p2-api-endpoints HEAD
```

## Before Sprint Ends

Make sure:

1. All work is committed
2. All branches are pushed
3. No uncommitted changes (`git status` should be clean)
4. Your branch is up to date with dev (`git rebase origin/dev`)

```bash
# Final check
git status
git log -5 --oneline
git diff origin/dev
```

## Questions?

Refer to this file, or check:
- `git help <command>` for any git command
- GitHub/GitLab's PR/merge request UI for status
- The project README.md for architecture overview
