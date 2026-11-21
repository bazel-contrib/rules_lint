"Define SQL linter aspects"

load("@rules_lint//lint:lint_test.bzl", "lint_test")
load("@rules_lint//lint:sqlfluff.bzl", "lint_sqlfluff_aspect")

sqlfluff = lint_sqlfluff_aspect(
    binary = Label("//tools/lint:sqlfluff"),
    configs = [
        Label("//:.sqlfluff"),
        Label("//src:nested/.sqlfluff"),
    ],
)

sqlfluff_test = lint_test(aspect = sqlfluff)
