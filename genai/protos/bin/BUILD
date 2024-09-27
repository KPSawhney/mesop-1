load("//build_defs:defaults.bzl", "THIRD_PARTY_PY_MYPY_PROTOBUF", "py_binary")

package(default_visibility = ["//visibility:public"])


py_binary(
    name = "protoc_gen_mypy",
    srcs = ["protoc_gen_mypy_wrapper.py"],
    main = "protoc_gen_mypy_wrapper.py",
    deps = THIRD_PARTY_PY_MYPY_PROTOBUF,
)
