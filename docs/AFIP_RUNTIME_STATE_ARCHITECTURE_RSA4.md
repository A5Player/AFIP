# AFIP Runtime State Architecture — RSA-4 Revision 2

## Drift Detection Hotfix

Revision 2 fixes false repository drift caused by Git collapsing untracked
contents into directory-level entries.

The preview now:

- requests `--untracked-files=all`;
- compares real file paths instead of collapsed directory placeholders;
- recognizes RSA report, repository hygiene, and production activation path
  families already covered by the approved RSA-3 contract.

Safety behavior remains unchanged: explicit apply, backup first, cached-only
untracking, no working-tree deletion, no commit, and no push.
