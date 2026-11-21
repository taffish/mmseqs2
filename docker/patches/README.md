# HTML label patch

`html-escape.patch` applies to MMseqs2 commit
`ab57c0b9cd8893f1063e391c94cc845a3179bab1` with zero fuzz.
It changes only alignment HTML string encoding and bounded Krona label output,
not sequence algorithms, TSV formatting, taxonomy assignment or counts.

The source context is Copyright © 2024 The MMseqs2 Development Team, under
the MIT license retained in [LICENSE.MMseqs2](LICENSE.MMseqs2). TAFFISH's
packaging additions retain the repository's Apache-2.0 license. The source
archive and patch have separate identities; this is not an unmodified binary.
