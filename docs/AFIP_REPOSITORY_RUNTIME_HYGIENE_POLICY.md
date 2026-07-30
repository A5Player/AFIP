# AFIP Repository Runtime Hygiene & Git Ignore Policy

## Purpose

Keep source, configuration, tests, and permanent documentation reviewable while preventing clearly temporary runtime artifacts from polluting `git status`.

## Safety rules

- No `git clean -fd`.
- No `git restore .`.
- No automatic deletion.
- No automatic untracking of files already committed.
- No blanket ignore for `runtime/` because AFIP contains permanent contracts, certification evidence, and intentional runtime fixtures.
- Research datasets and certification records must be reviewed before any ignore or removal decision.

## Safe ignore scope

The installer manages only these clearly temporary patterns:

```gitignore
patch_backups/
runtime/**/*.pid
runtime/pytest_temp/
runtime/pytest_tmp/
status_after_start.txt
```

## Important limitation

`.gitignore` does not hide files already tracked by Git. Modified tracked runtime files remain visible until AFIP explicitly chooses one of these policies per file:

1. Keep tracked and commit intentional snapshots.
2. Keep tracked but restore generated changes after validation.
3. Migrate the generated output to an ignored runtime location, preserving backward compatibility.
4. Remove from tracking only after source and consumer review.

This pack performs an audit and reports candidates. It does not make that decision automatically.
