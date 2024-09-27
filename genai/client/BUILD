load(
    "//build_defs:defaults.bzl",
    "py_library",
    "THIRD_PARTY_PY_GRPC"
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "client",
    srcs = glob(
        ["*.py"],
        exclude = [
            "*_test.py",
        ],
    ),
    deps = [
               "//genai/content:content",
               "//genai/actions:actions",
           ] + THIRD_PARTY_PY_GRPC
)
