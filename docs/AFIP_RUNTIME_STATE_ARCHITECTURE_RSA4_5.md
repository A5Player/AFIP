# AFIP Runtime State Architecture — RSA-4.5

RSA-4.5 reconciles generated runtime paths that became tracked after the RSA-3
planning snapshot.

The pack discovers all currently tracked paths covered by the approved RSA-4
runtime policy, excludes paths already staged for cached-only removal, verifies
that each candidate still exists in the working tree, and applies only
`git rm --cached`.

It stages only the RSA-4.5 source files. It does not delete working-tree files,
commit, push, archive, move, restore, or modify runtime data.
