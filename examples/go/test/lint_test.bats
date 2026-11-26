bats_load_library "bats-support"
bats_load_library "bats-assert"

@test "fail_on_violation fails the build and prints the findings" {
	run bazel build --config=lint --@rules_lint//lint:fail_on_violation //src:hello
	assert_failure
	assert_output --partial "govet: 1"
}

@test "fail_on_violation passes a clean package" {
	run bazel build --config=lint --@rules_lint//lint:fail_on_violation //src:greeting
	assert_success
}
