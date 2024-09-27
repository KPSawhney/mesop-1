load(
    "//build_defs:defaults.bzl",
    "py_library",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "actions",
    srcs = glob(
        ["*.py"],
        exclude = [
            "*_test.py",
        ],
    ),
    deps = [
                "//genai/content:content",
                "//genai/protos:genai_py_pb2"
           ]
)
