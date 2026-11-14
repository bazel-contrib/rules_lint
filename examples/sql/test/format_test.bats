bats_load_library "bats-support"
bats_load_library "bats-assert"

setup() {
    fixture_dir="$(mktemp -d .format-test.XXXXXX)"
    cd "$fixture_dir"
    cat > .sqlfluff <<'CONFIG'
[sqlfluff]
dialect = ansi

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper
CONFIG
    echo 'select 1 from dual' > query.sql
}

teardown() {
    cd ..
    rm -rf "$fixture_dir"
}

@test "sqlfluff checks and fixes SQL using local configuration" {
    run bazel run //tools/format:format_sqlfluff_SQL_with_sqlfluff.check -- query.sql
    assert_failure
    assert_output --partial "CP01"
    [ "$(cat query.sql)" = 'select 1 from dual' ]

    run bazel run //tools/format:format_sqlfluff_SQL_with_sqlfluff -- query.sql
    assert_success
    [ "$(cat query.sql)" = 'SELECT 1 FROM dual' ]

    run bazel run //tools/format:format_sqlfluff_SQL_with_sqlfluff.check -- query.sql
    assert_success
}
