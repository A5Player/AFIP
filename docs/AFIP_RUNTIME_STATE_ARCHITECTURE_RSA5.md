# AFIP Runtime State Architecture — RSA-5 Revision 3

Revision 3 fixes report rendering compatibility. The certification report uses
`manual_review_warnings`; the Markdown renderer now reads that key and retains
backward compatibility with the former `manual_review` key.

No certification policy, Git state, staged files, runtime data, or working-tree
files are changed by this hotfix.
