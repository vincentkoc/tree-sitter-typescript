from unittest import TestCase, expectedFailure
import json
from pathlib import Path

import tree_sitter, tree_sitter_typescript


class TestLanguage(TestCase):
    def test_can_load_typescript_grammar(self):
        try:
            tree_sitter.Language(tree_sitter_typescript.language_typescript())
        except Exception:
            self.fail("Error loading TypeScript grammar")

    def test_can_load_tsx_grammar(self):
        try:
            tree_sitter.Language(tree_sitter_typescript.language_tsx())
        except Exception:
            self.fail("Error loading TSX grammar")


class TestTypeCoverage(TestCase):
    def parsers(self):
        for dialect, language in (
            ("typescript", tree_sitter_typescript.language_typescript),
            ("tsx", tree_sitter_typescript.language_tsx),
        ):
            yield dialect, tree_sitter.Parser(tree_sitter.Language(language()))

    def test_import_types_and_exports(self):
        sources = (
            'export type * from "./types";',
            'export type * as Types from "./types";',
            'let entries: import("node:fs").Dirent[];',
            'type Result = import("./types").Result<string>;',
            'type Results = import("./types").Result<string>[][];',
            'type Value = import("./types").Result["value"];',
            'type Results = (import("./types").Result)[];',
            "const actual = await load<Module>()();",
            "const actual = await load<Module>().value;",
            "const actual = await load<Module>()[index];",
            "const actual = await load!<Module>();",
            'const actual = await importOriginal<typeof import("./module")>();',
            'const actual = await vi.importActual<typeof import("./module")>("./module",);',
        )
        for dialect, parser in self.parsers():
            for source in sources:
                with self.subTest(dialect=dialect, source=source):
                    encoded = source.encode()
                    root = parser.parse(encoded).root_node
                    self.assertFalse(root.has_error, str(root))
                    self.assertEqual(root.text, encoded)

    def test_await_owns_the_complete_call(self):
        expressions = (
            'await importOriginal<typeof import("./module")>()',
            'await vi.importActual<typeof import("./module")>("./module",)',
            'await load<Module>()',
        )
        for dialect, parser in self.parsers():
            for expression in expressions:
                with self.subTest(dialect=dialect, expression=expression):
                    root = parser.parse(f"const value = {expression};".encode()).root_node
                    self.assertFalse(root.has_error, str(root))
                    declaration = root.named_children[0].named_children[0]
                    value = declaration.child_by_field_name("value")
                    self.assertEqual(value.type, "await_expression")
                    self.assertEqual(value.named_children[0].type, "call_expression")

    def test_invalid_syntax_still_fails(self):
        sources = (
            'export type * from;',
            'type Broken = import("./types").;',
            'const actual = await read<typeof import("./module")>(;',
        )
        for dialect, parser in self.parsers():
            for source in sources:
                with self.subTest(dialect=dialect, source=source):
                    self.assertTrue(parser.parse(source.encode()).root_node.has_error)

    def test_comparisons_remain_expressions(self):
        for dialect, parser in self.parsers():
            for expression in ("left < typeof right", "left < right > other", "left < await right", "left < ++right"):
                with self.subTest(dialect=dialect, expression=expression):
                    root = parser.parse(f"const value = {expression};".encode()).root_node
                    self.assertFalse(root.has_error, str(root))
                    value = root.named_children[0].named_children[0].child_by_field_name("value")
                    self.assertEqual(value.type, "binary_expression")

    def test_generic_callees_keep_their_shape(self):
        cases = (
            ("await load()", "await_expression", "call_expression"),
            ('await import("./module")', "await_expression", "call_expression"),
            ("(await load)<Module>()", "call_expression", "parenthesized_expression"),
            ("new Factory<Module>()()", "call_expression", "new_expression"),
            ("new Factory<Module>()", "new_expression", "identifier"),
            ("obj.method?.<Module>()", "call_expression", "member_expression"),
            ("obj?.method<Module>()", "call_expression", "member_expression"),
            ("(factory as Callable)<Module>()", "call_expression", "parenthesized_expression"),
            ('(import("./module")).then(done)', "call_expression", "member_expression"),
        )
        for dialect, parser in self.parsers():
            for expression, outer, operand in cases:
                with self.subTest(dialect=dialect, expression=expression):
                    root = parser.parse(f"const value = {expression};".encode()).root_node
                    self.assertFalse(root.has_error, str(root))
                    value = root.named_children[0].named_children[0].child_by_field_name("value")
                    self.assertEqual(value.type, outer)
                    self.assertEqual(value.named_children[0].type, operand)

    def test_chained_generic_await(self):
        failures = []
        for dialect, parser in self.parsers():
            for expression in (
                "await load<Module>()()",
                "await load<Module>().value",
                "await load<Module>()[index]",
                "await load!<Module>()",
            ):
                root = parser.parse(f"const value = {expression};".encode()).root_node
                value = root.named_children[0].named_children[0].child_by_field_name("value")
                if root.has_error or value.type != "await_expression":
                    failures.append((dialect, expression, str(root)))
        self.assertEqual(failures, [])

    reference = json.loads(Path(__file__).with_name("await_ownership.json").read_text())
    shape_types = {
        shape[0]
        for entry in [*reference["cases"], *reference["known_gaps"].values()]
        for shape in entry["shapes"]
    }

    def assert_compiler_shapes(self, parser, entry, old_tree=None):
        prefix = self.reference["reference"]["prefix"].encode()
        source = prefix + entry["expression"].encode() + self.reference["reference"]["suffix"].encode()
        tree = parser.parse(source, old_tree) if old_tree is not None else parser.parse(source)
        root = tree.root_node
        self.assertFalse(root.has_error, str(root))
        shapes = []
        pending = [root]
        while pending:
            node = pending.pop()
            if node.type in self.shape_types:
                shapes.append([node.type, node.start_byte - len(prefix), node.end_byte - len(prefix)])
            pending.extend(node.named_children)
        self.assertEqual(sorted(shapes), sorted(entry["shapes"]), entry["expression"])
        return tree

    def test_await_matches_compiler_shapes(self):
        for dialect, parser in self.parsers():
            for entry in self.reference["cases"]:
                with self.subTest(dialect=dialect, expression=entry["expression"]):
                    self.assert_compiler_shapes(parser, entry)

    def test_await_invalid_follow_tokens(self):
        for dialect, parser in self.parsers():
            for expression in self.reference["invalid_cases"]:
                with self.subTest(dialect=dialect, expression=expression):
                    source = "async function task(){const value = " + expression + ";}"
                    self.assertTrue(parser.parse(source.encode()).root_node.has_error)

    def assert_known_gap(self, *names):
        failures = []
        for dialect, parser in self.parsers():
            for name in names:
                try:
                    self.assert_compiler_shapes(parser, self.reference["known_gaps"][name])
                except AssertionError as error:
                    failures.append((dialect, name, str(error)))
        self.assertEqual(failures, [])

    @expectedFailure
    def test_unary_generic_call_known_gap(self):
        self.assert_known_gap("unary_generic_call")

    @expectedFailure
    def test_generic_tagged_template_known_gap(self):
        self.assert_known_gap("generic_tagged_template")

    @expectedFailure
    def test_await_cast_known_gaps(self):
        self.assert_known_gap("non_null_cast", "instantiation_cast")

    @expectedFailure
    def test_instantiation_newline_known_gap(self):
        self.assert_known_gap(*(
            name for name in self.reference["known_gaps"] if name.startswith("instantiation_")
        ))

    @expectedFailure
    def test_combined_shift_assignment_known_gap(self):
        failures = []
        for dialect, parser in self.parsers():
            for expression in self.reference["known_invalid_cases"]:
                source = self.reference["reference"]["prefix"] + expression + self.reference["reference"]["suffix"]
                if not parser.parse(source.encode()).root_node.has_error:
                    failures.append((dialect, expression))
        self.assertEqual(failures, [])

    def test_instantiation_incremental_lookahead(self):
        entries = {entry["expression"]: entry for entry in self.reference["cases"]}
        before = entries["await f<T> /* comment */ + value"]
        after = entries["await f<T> /* comment */ / value"]
        for dialect, parser in self.parsers():
            with self.subTest(dialect=dialect):
                tree = self.assert_compiler_shapes(parser, before)
                position = len(self.reference["reference"]["prefix"]) + before["expression"].index("+")
                for entry in (after, before):
                    tree.edit(
                        start_byte=position, old_end_byte=position + 1, new_end_byte=position + 1,
                        start_point=(0, position), old_end_point=(0, position + 1),
                        new_end_point=(0, position + 1),
                    )
                    tree = self.assert_compiler_shapes(parser, entry, old_tree=tree)
