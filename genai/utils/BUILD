load("//build_defs:defaults.bzl", "PYTHON_RUNFILES_DEP", "py_library")

package(default_visibility = ["//visibility:public"])


py_library(
    name = "utils",
    srcs = glob(
        ["*.py"],
        exclude = ["*_test.py"],
    ),
    deps = PYTHON_RUNFILES_DEP
)
