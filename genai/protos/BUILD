load("//build_defs:defaults.bzl", "proto_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])


proto_library(
    name = "genai_proto",
    srcs = ["genai.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:timestamp_proto",
    ]
)

py_proto_library(
    name = "genai_py_pb2",
    deps = [":genai_proto"],
)
