load("//build_defs:defaults.bzl", "proto_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])


proto_library(
    name = "genai_proto",
    srcs = ["genai.proto"],
)

py_proto_library(
    name = "genai_py_pb2",
    deps = [":genai_proto"],
)
