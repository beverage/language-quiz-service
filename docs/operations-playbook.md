# Operations Playbook

This playbook documents common operational tasks for the Language Quiz Service using the `lqs` CLI.

## Table of Contents

- [Bulk Deletion Operations](#bulk-deletion-operations)
  - [Problem Cleanup](#problem-cleanup)
  - [Generation Request Cleanup](#generation-request-cleanup)
- [Quick Reference](#quick-reference)

---

## Bulk Deletion Operations

### Problem Cleanup

The `lqs problem purge` command provides efficient bulk deletion with flexible filtering.

#### Delete Problems by Age

```bash
# Delete problems older than 7 days
lqs problem purge --older-than 7d --force

# Delete problems older than 2 weeks
lqs problem purge --older-than 2w --force

# Delete problems created before a specific date
lqs problem purge --older-than 2025-01-01 --force
```

#### Delete Problems in a Date Range

```bash
# Delete problems created between 7 days and 1 day ago
lqs problem purge --newer-than 7d --older-than 1d --force
```

#### Delete Problems by Topic

```bash
# Delete all problems tagged with "test_data"
lqs problem purge --topic test_data --force

# Delete problems with multiple topic tags
lqs problem purge --topic test_data --topic cleanup --force
```

#### Combined Filters

```bash
# Delete test problems older than 2 days
lqs problem purge --older-than 2d --topic test_data --force

# Delete old test problems in a specific date range
lqs problem purge --newer-than 30d --older-than 7d --topic test_data --force
```

#### Interactive Mode (Dry Run)

Omit `--force` to see what will be deleted and confirm:

```bash
# Shows count and asks for confirmation
lqs problem purge --older-than 7d

# Example output:
# 🎯 Found 42 problems with created before 2025-01-01 12:00
# ⚠️  This will delete 42 problems.
# Continue? [y/N]:
```

---

### Generation Request Cleanup

Use `lqs generation-request clean` to remove old completed, failed, or expired generation requests.

#### Basic Cleanup

```bash
# Delete completed/failed requests older than 7 days
lqs generation-request clean --older-than 7d --force

# Delete requests older than 24 hours
lqs generation-request clean --older-than 24h --force
```

#### Filter by Topic

```bash
# Delete old test generation requests
lqs generation-request clean --older-than 1d --topic test_data --force
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Delete problems older than N days | `lqs problem purge --older-than Nd -f` |
| Delete test problems | `lqs problem purge --topic test_data -f` |
| Delete old test problems | `lqs problem purge --older-than 2d --topic test_data -f` |
| Delete problems in date range | `lqs problem purge --newer-than 7d --older-than 1d -f` |
| Delete problems before date | `lqs problem purge --older-than 2025-01-01 -f` |
| Clean old generation requests | `lqs generation-request clean --older-than 7d -f` |
| Preview deletion (no --force) | `lqs problem purge --older-than 7d` |

### Duration Formats

The `--older-than` and `--newer-than` options accept:

| Format | Example | Meaning |
|--------|---------|---------|
| Minutes | `30m` | 30 minutes ago |
| Hours | `2h` | 2 hours ago |
| Days | `7d` | 7 days ago |
| Weeks | `2w` | 2 weeks ago |
| Combined | `1d12h` | 1 day and 12 hours ago |
| Absolute date | `2025-01-01` | January 1, 2025 |
| Absolute datetime | `2025-01-01T12:00:00` | January 1, 2025 at noon UTC |

### Safety Notes

- **Remote purge is forbidden**: The `purge` command only works on local databases for safety.
- **Always preview first**: Run without `--force` to see what will be deleted.
- **Use topic tags**: Tag test data with `test_data` for easy cleanup.
