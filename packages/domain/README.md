# poseperfect_domain

The pure domain: poses, attempts, references, scoring rules.

Fixed by issue [#6](https://github.com/grez-lucas/poseperfect/issues/6): this
package declares **no dependencies at all**. Not Flutter, not Riverpod, not
drift. That is the inward rule, and `depend_on_referenced_packages` is set to
`error` so CI enforces it rather than a convention doing so.

No codegen lives here either - Dart 3 sealed classes for unions, hand-written
`copyWith`.
