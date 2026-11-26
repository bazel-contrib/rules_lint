load("@rules_go//go:def.bzl", "go_library")

go_library(
    name = "consumer",
    srcs = ["consumer.go"],
    importpath = "example.com/samename/consumer",
    visibility = ["//visibility:public"],
    deps = [
        "//test/samename/internal/language",
        "//test/samename/language",
    ],
)
