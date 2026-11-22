setup() {
    fixture_dir="$(mktemp -d .format-test.XXXXXX)"
    cd "$fixture_dir"
    echo 'ignored.rb rules-lint-ignored' > .gitattributes
    echo 'numbers=[1,2,3]' > source.rb
    echo 'numbers=[4,5,6]' > task.rake
    echo 'ignored=[1,2,3]' > ignored.rb
    ln -s ignored.rb alias.rb
}

teardown() {
    cd ..
    rm -rf "$fixture_dir"
}

@test "rubyfmt checks and fixes Ruby and Rake files without changing excluded or symlinked inputs" {
    run bazel run //tools/format:format.check
    [ "$status" -ne 0 ]
    [[ "$output" == *'+++ source.rb'* ]]
    [[ "$output" == *'+++ task.rake'* ]]
    [ "$(cat source.rb)" = 'numbers=[1,2,3]' ]
    [ "$(cat task.rake)" = 'numbers=[4,5,6]' ]

    run bazel run //tools/format
    [ "$status" -eq 0 ]
    [ "$(cat source.rb)" = 'numbers = [1, 2, 3]' ]
    [ "$(cat task.rake)" = 'numbers = [4, 5, 6]' ]
    [ "$(cat ignored.rb)" = 'ignored=[1,2,3]' ]
    [ -L alias.rb ]

    run bazel run //tools/format:format.check
    [ "$status" -eq 0 ]
}
