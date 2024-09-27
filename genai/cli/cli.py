from typing import Sequence

from absl import app, flags

from genai.cli.execute_module import (
    clear_app_modules,
    execute_module,
    get_module_name_from_runfile_path,
)
from genai.utils.runfiles import get_runfile_location

FLAGS = flags.FLAGS

flags.DEFINE_string("path", "", "path to main python module of Genai API.")


def execute_main_module():
    module_name = get_module_name_from_runfile_path(FLAGS.path)
    clear_app_modules(module_name=module_name)
    execute_module(
        module_path=get_runfile_location(FLAGS.path),
        module_name=module_name,
    )


def main(argv: Sequence[str]):
    if len(FLAGS.path) < 1:
        raise Exception("Required flag 'path'. Received: " + FLAGS.path)

    try:
        execute_main_module()
    except Exception as e:
        raise e

    print('Executed main module!')


if __name__ == "__main__":
    app.run(main)
