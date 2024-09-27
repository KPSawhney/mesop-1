# Description:
#   TODO(KPSawhney): Genai API description
load("//build_defs:defaults.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

exports_files(["LICENSE"])

py_library(
    name = "genai",
    srcs = [
        "__init__.py",
    ],
    data = glob([".env"]),
    deps = [
        "//genai/actions",
        "//genai/client",
        "//genai/content",
    ],
)

py_library(
    name = "index",
    srcs = ["index.py"],
    deps = [
        "//genai",
    ],
)
