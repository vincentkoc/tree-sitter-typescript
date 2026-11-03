# Changelog

## 0.23.2+vk.2 - 2026-11-03

- Keep generic calls and postfix chains inside their await expressions.
- Preserve comparison parsing with a token-aware instantiation boundary.
- Add reproducible TypeScript 6.0.3 expression-shape references, invalid syntax
  controls and incremental lookahead checks for both native grammars.
- Promote the original await regressions to passing tests and record the
  remaining compiler-reference gaps explicitly.

## 0.23.2+vk.1 - 2026-11-03

- Accept type-only wildcard exports and import member type arguments.
- Support array, indexed and parenthesized import types without rewriting source.
- Resolve `typeof import()` generic calls and test the remaining await AST gap,
  invalid syntax, comparisons, and runtime import expressions in TS and TSX.
- Ship ABI 14 generated parsers for Git-pinned Python consumers. See the README
  for upstream contributions, build requirements and generator versions.
