load("@npm//:prettier/package_json.bzl", prettier = "bin")
load("@rules_lint//format:defs.bzl", "format_multirun")

package(default_visibility = ["//:__subpackages__"])

prettier.prettier_binary(
    name = "prettier",
    env = {"BAZEL_BINDIR": "."},
)

format_multirun(
    name = "format",
    visibility = ["//:__subpackages__"],
    yaml = ":prettier",
)
