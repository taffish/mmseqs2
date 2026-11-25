# HTML label patch

`html-escape.patch` applies to MMseqs2 commit
`ae60ef6964f3de689139bcfe290d9fad18f70b06` with zero fuzz.
It changes only alignment HTML string encoding and bounded Krona label output,
not sequence algorithms, TSV formatting, taxonomy assignment or counts.

The source context is Copyright © 2024 The MMseqs2 Development Team, under
the MIT license retained in [LICENSE.MMseqs2](LICENSE.MMseqs2). TAFFISH's
packaging additions retain the repository's Apache-2.0 license. The source
archive and patch have separate identities; this is not an unmodified binary.
