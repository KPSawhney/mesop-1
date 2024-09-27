load(
    "//build_defs:defaults.bzl",
    "THIRD_PARTY_PY_ABSL_PY",
    "py_binary",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])


COMMON_DATA = [
    "//genai:index",
]

COMMON_DEPS = (
    [
        ":execute_module",
        "//genai",  # Keep dep to ensure the entire Genai library is loaded.
    ] + THIRD_PARTY_PY_ABSL_PY
)

exports_files(["cli.py"])

py_library(
    name = "cli_lib",
    srcs = ["cli.py"],
    deps = COMMON_DEPS,
)

# Prod CLI
py_binary(
    name = "cli",
    srcs = ["cli.py"],
    data = COMMON_DATA,
    main = "cli.py",
    deps = [":cli_lib"],
)

py_library(
    name = "execute_module",
    srcs = [
        "__init__.py",
        "execute_module.py",
    ],
)
