# tree-sitter-typescript

[![CI][ci]](https://github.com/tree-sitter/tree-sitter-typescript/actions/workflows/ci.yml)
[![discord][discord]](https://discord.gg/w7nTvsVJhm)
[![matrix][matrix]](https://matrix.to/#/#tree-sitter-chat:matrix.org)
[![crates][crates]](https://crates.io/crates/tree-sitter-typescript)
[![npm][npm]](https://www.npmjs.com/package/tree-sitter-typescript)
[![pypi][pypi]](https://pypi.org/project/tree-sitter-typescript)

TypeScript and TSX grammars for [tree-sitter][].

## Python source fork

This fork supplies `tree-sitter-typescript==0.23.2+vk.2` to
[scb-check](https://github.com/vincentkoc/scb-check) through an exact Git revision.
It is not a registry release. Installing from Git builds the checked-in C parsers
and requires a C compiler and Python development headers; Node.js is needed only
to regenerate them. Both grammars retain Tree-sitter ABI 14.

The fork backports type-only wildcard exports from
[PR #358](https://github.com/tree-sitter/tree-sitter-typescript/pull/358)
by Gunnlaugur Thor Briem, import member type arguments from
[PR #365](https://github.com/tree-sitter/tree-sitter-typescript/pull/365)
by Nicolas Marchildon (following Herrington Darkholme's earlier work), and
`typeof import()` call precedence from
[PR #375](https://github.com/tree-sitter/tree-sitter-typescript/pull/375)
by Donald Wasserman. It extends import types to array, indexed and parenthesized
forms and tests expression/type ambiguity. It also fixes the
[generic-await ownership bug](https://github.com/tree-sitter/tree-sitter-typescript/issues/282)
for calls and postfix chains, preserving comparisons, constructors and explicit
parentheses. A scanner guard distinguishes instantiations from comparisons using
the following token and intervening line breaks.

Python regressions compare expression kinds and UTF-8 byte ranges against
TypeScript 6.0.3 in async function bodies. The checked-in reference data needs no
TypeScript installation during tests. To regenerate it, pass an installed 6.0.3
package directory to `node bindings/python/tests/await_oracle.cjs /path/to/typescript`.
The compiler source and version are recorded in the fixture.

Known gaps remain explicit: unary generic calls, generic tagged templates,
await casts involving non-null assertions or bare instantiations, newline updates
after instantiations, and malformed
combined shift assignments. Their reference cases are expected failures, not
passing coverage. Parse success does not imply full TypeScript AST correctness;
this fork changes the parser, not application source.

Generated sources use `tree-sitter-cli@0.24.4`,
`tree-sitter-javascript@0.23.1`, and `tree-sitter generate --abi 14` from each
of `typescript/` and `tsx/`. CI verifies generation is reproducible and runs
the native corpus and Python binding regressions. The upstream MIT license
and author metadata remain intact.


Because TSX and TypeScript are actually two different dialects, this module defines two grammars. Require them as follows:

```js
require("tree-sitter-typescript").typescript; // TypeScript grammar
require("tree-sitter-typescript").tsx; // TSX grammar
```

For Javascript files with [flow] type annotations you can use the `tsx` parser.

[tree-sitter]: https://github.com/tree-sitter/tree-sitter
[flow]: https://flow.org/en/

References

- [TypeScript Language Spec](https://github.com/microsoft/TypeScript/blob/30cb20434a6b117e007a4959b2a7c16489f86069/doc/spec-ARCHIVED.md)

[ci]: https://img.shields.io/github/actions/workflow/status/tree-sitter/tree-sitter-typescript/ci.yml?logo=github&label=CI
[discord]: https://img.shields.io/discord/1063097320771698699?logo=discord&label=discord
[matrix]: https://img.shields.io/matrix/tree-sitter-chat%3Amatrix.org?logo=matrix&label=matrix
[npm]: https://img.shields.io/npm/v/tree-sitter-typescript?logo=npm
[crates]: https://img.shields.io/crates/v/tree-sitter-typescript?logo=rust
[pypi]: https://img.shields.io/pypi/v/tree-sitter-typescript?logo=pypi&logoColor=ffd242
