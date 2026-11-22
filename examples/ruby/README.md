# Ruby Formatting and Linting Example

This example demonstrates how to set up formatting and linting for Ruby code using `rules_lint`.

## Supported Tools

### Linters

- **RuboCop** - Ruby static code analyzer
- **Standard Ruby** - Zero-configuration Ruby style guide and linter based on RuboCop

### Formatter

- **[rubyfmt](https://github.com/fables-tales/rubyfmt)** formats `.rb` and `.rake` files.

### Formatting setup

[tools/format/BUILD](tools/format/BUILD) uses the prebuilt `@rules_lint//format:rubyfmt`
executable. Run from this example's directory:

```sh
bazel run //tools/format
bazel run //tools/format:format.check
# Limit formatting to selected files:
bazel run //tools/format -- src/hello.rb
```

See [formatting setup](../../docs/formatting.md) for supported platforms, file exclusions,
and custom arguments.

## Setup

1. Configure MODULE.bazel with required dependencies
2. Configure the Aspect CLI lint task in `.aspect/config.axl`
3. Configure Linters

- See `tools/lint/linters.bzl` for how to set up each linter aspect

4. Perform linting using `aspect lint`

## Example Code

The `src/` directory contains example Ruby files with intentional violations:

- `hello.rb` - Contains RuboCop and Standard Ruby violations (unused variables, line length, indentation, string literals, trailing commas)

## Configuration Files

- `.rubocop.yml` - RuboCop configuration
- `.standard.yml` - Standard Ruby configuration
- `Gemfile` - Ruby gem dependencies
- `.ruby-version` - Ruby version specification
