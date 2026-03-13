# Plan 1: Reset & Backup

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Back up all GitHub issues and templates, then clean the repository of all old source code and config files, preserving git history.

**Architecture:** Export issues via `gh` CLI to JSON, copy template files, then delete old source/config in a single commit. Git history is preserved — no force-push.

**Tech Stack:** gh CLI, git, bash

**Spec:** `docs/superpowers/specs/2026-03-13-vue-playground-reset-design.md` — see "Reset Procedure" section.

---

## Chunk 1: Backup & Clean

### Task 1: Export GitHub Issues

**Files:**
- Create: `backup/issues/` directory with JSON files

- [ ] **Step 1: Export all issues to JSON**

```bash
mkdir -p backup/issues
gh issue list --state all --json number,title,body,labels,state,createdAt,closedAt --limit 50 > backup/issues/all-issues.json
```

- [ ] **Step 2: Export each issue individually (preserving comments)**

Extract issue numbers dynamically from the exported list:

```bash
for i in $(jq '.[].number' backup/issues/all-issues.json); do
  gh issue view "$i" --json number,title,body,labels,state,comments > "backup/issues/issue-${i}.json"
done
```

- [ ] **Step 3: Verify backup**

Run: `ls -la backup/issues/ && jq '.| length' backup/issues/all-issues.json`
Expected: `all-issues.json` + one `issue-N.json` per issue. The `jq` command should print `11`.

- [ ] **Step 4: Commit backup**

```bash
git add backup/issues/
git commit -m "backup: export all 11 GitHub issues to JSON"
```

---

### Task 2: Backup Issue Template

**Files:**
- Create: `backup/templates/user-story.md`

- [ ] **Step 1: Copy template**

```bash
mkdir -p backup/templates
cp .github/ISSUE_TEMPLATE/user-story.md backup/templates/user-story.md
```

- [ ] **Step 2: Commit**

```bash
git add backup/templates/
git commit -m "backup: copy issue template"
```

---

### Task 3: Clean Old Source and Config Files

**Files:**
- Delete: `src/` (entire directory)
- Delete: `vite.config.ts`, `vitest.config.ts`
- Delete: `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `tsconfig.vitest.json`
- Delete: `index.html`, `env.d.ts`
- Delete: `package.json`, `package-lock.json`
- Delete: `.eslintrc.cjs`, `.prettierrc.json`
- Delete: `postcss.config.js`, `tailwind.config.js`
- Delete: `.vscode/` directory
- Delete: `public/` directory (contains old favicon — will be recreated in Plan 2)
- Keep: `draft-for-blogs/`, `backup/`, `.github/`, `.claude/`, `README.md`, `docs/`, `.git/`, `.gitignore`
- Note: `node_modules/` is untracked (.gitignore) — removed locally but won't appear in the commit

- [ ] **Step 1: Delete old files**

```bash
rm -rf src/ .vscode/ node_modules/ public/
rm -f vite.config.ts vitest.config.ts index.html env.d.ts
rm -f tsconfig.json tsconfig.app.json tsconfig.node.json tsconfig.vitest.json
rm -f package.json package-lock.json
rm -f .eslintrc.cjs .prettierrc.json
rm -f postcss.config.js tailwind.config.js
```

- [ ] **Step 2: Verify only preserved files remain**

Run: `ls -la`
Expected: Only `.git/`, `.github/`, `.claude/`, `.gitignore`, `README.md`, `docs/`, `draft-for-blogs/`, `backup/`

- [ ] **Step 3: Commit clean slate**

```bash
git add -u
git commit -m "chore: remove old shop source code and config

Preserve git history, backup/, draft-for-blogs/, docs/, .github/"
```
