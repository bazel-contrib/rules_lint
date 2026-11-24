"Re-exports the parts of the root module's rules_rust that rules_lint uses."

load("{rules_rust}//rust:defs.bzl", _rust_clippy_action = "rust_clippy_action")
load("{rules_rust}//rust:rust_common.bzl", _CrateInfo = "CrateInfo", _TestCrateInfo = "TestCrateInfo")

rules_rust = struct(
    CrateInfo = _CrateInfo,
    TestCrateInfo = _TestCrateInfo,
    rust_clippy_action = _rust_clippy_action,
    toolchain_type = Label("{rules_rust}//rust:toolchain_type"),
)
