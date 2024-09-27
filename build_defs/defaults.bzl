"""Wrapper for commonly used Bazel rules.
"""

load("@aspect_rules_py//py:defs.bzl", _py_binary = "py_binary", _py_library = "py_library", _py_test = "py_test")
load("@my_deps//:requirements.bzl", "requirement")
load("@rules_proto//proto:defs.bzl", _proto_library = "proto_library")
load("//build_defs:py_proto_library.bzl", _py_proto_library = "py_proto_library")

# Re-export symbols
proto_library = _proto_library
py_binary = _py_binary
py_library = _py_library
py_proto_library = _py_proto_library
py_test = _py_test

PYTHON_RUNFILES_DEP = [
    "@rules_python//python/runfiles",
]

THIRD_PARTY_PY_ABSL_PY = [
    requirement("absl-py"),
]

THIRD_PARTY_PY_MYPY_PROTOBUF = [
    requirement("mypy-protobuf"),
]

THIRD_PARTY_PY_DOTENV = [
    requirement("python-dotenv"),
]

THIRD_PARTY_PY_GRPCIO = [
    requirement("grpcio"),
]
