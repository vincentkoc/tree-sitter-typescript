// Regenerate using an installed TypeScript 6.0.3 package; no compiler is needed
// to run the Python regressions against the checked-in reference shapes.
const fs = require('node:fs');
const path = require('node:path');
const ts = require(process.argv[2] || 'typescript');
const target = path.join(__dirname, 'await_ownership.json');
const fixture = JSON.parse(fs.readFileSync(target, 'utf8'));
if (ts.version !== fixture.reference.version) {
  throw new Error(`Expected TypeScript ${fixture.reference.version}, got ${ts.version}`);
}
const kinds = {
  AwaitExpression: 'await_expression',
  CallExpression: 'call_expression',
  TaggedTemplateExpression: 'call_expression',
  PropertyAccessExpression: 'member_expression',
  ElementAccessExpression: 'subscript_expression',
  NonNullExpression: 'non_null_expression',
  ExpressionWithTypeArguments: 'instantiation_expression',
  NewExpression: 'new_expression',
  BinaryExpression: 'binary_expression',
  AsExpression: 'as_expression',
  SatisfiesExpression: 'satisfies_expression',
  ConditionalExpression: 'ternary_expression',
  ParenthesizedExpression: 'parenthesized_expression',
  VoidExpression: 'unary_expression',
  TypeOfExpression: 'unary_expression',
  DeleteExpression: 'unary_expression',
};
for (const entry of [...fixture.cases, ...Object.values(fixture.known_gaps)]) {
  const prefix = fixture.reference.prefix;
  const source = prefix + entry.expression + fixture.reference.suffix;
  const file = ts.createSourceFile('test.ts', source,
    ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  if (file.parseDiagnostics.length) throw new Error(`Invalid reference: ${entry.expression}`);
  const shapes = [];
  function walk(node) {
    const name = ts.SyntaxKind[node.kind];
    let kind = kinds[name];
    if (name === 'PrefixUnaryExpression' || name === 'PostfixUnaryExpression') {
      kind = [ts.SyntaxKind.PlusPlusToken, ts.SyntaxKind.MinusMinusToken].includes(node.operator)
        ? 'update_expression' : 'unary_expression';
    }
    if (kind) shapes.push([kind,
      Buffer.byteLength(source.slice(prefix.length, node.getStart(file)), 'utf8'),
      Buffer.byteLength(source.slice(prefix.length, node.end), 'utf8')]);
    ts.forEachChild(node, walk);
  }
  walk(file);
  entry.shapes = shapes.sort((a, b) => a[0].localeCompare(b[0]) || a[1] - b[1] || a[2] - b[2]);
}
for (const expression of [...fixture.invalid_cases, ...fixture.known_invalid_cases]) {
  const source = fixture.reference.prefix + expression + fixture.reference.suffix;
  const file = ts.createSourceFile('test.ts', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  if (!file.parseDiagnostics.length) throw new Error(`Expected an invalid reference: ${expression}`);
}
fs.writeFileSync(target, JSON.stringify(fixture, null, 2) + '\n');
