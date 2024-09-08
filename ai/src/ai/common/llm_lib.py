import json
import re
from os import getenv
from typing import NamedTuple

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import (
  ChatCompletionMessageParam,
)

load_dotenv()

EDIT_HERE_MARKER = " # <--- EDIT HERE"


class ApplyPatchResult(NamedTuple):
  has_error: bool
  result: str


def read_file(filepath: str) -> str:
  with open(filepath) as f:
    return f.read().strip()


def apply_patch(original_code: str, patch: str) -> ApplyPatchResult:
  # Extract the diff content
  diff_pattern = r"<<<<<<< ORIGINAL(.*?)=======\n(.*?)>>>>>>> UPDATED"
  matches = re.findall(diff_pattern, patch, re.DOTALL)
  patched_code = original_code
  if len(matches) == 0:
    print("[WARN] No diff found:", patch)
    return ApplyPatchResult(
      True,
      "[AI-001] Sorry! AI output was mis-formatted. Please try again.",
    )
  for original, updated in matches:
    original = original.strip().replace(EDIT_HERE_MARKER, "")
    updated = updated.strip().replace(EDIT_HERE_MARKER, "")

    # Replace the original part with the updated part
    new_patched_code = patched_code.replace(original, updated, 1)
    if new_patched_code == patched_code:
      return ApplyPatchResult(
        True,
        "[AI-002] Sorry! AI output could not be used. Please try again.",
      )
    patched_code = new_patched_code

  return ApplyPatchResult(False, patched_code)


DEFAULT_MODEL = "ft:gpt-4o-mini-2024-07-18:mesop:small-prompt:A1472X3c"
DEFAULT_CLIENT = OpenAI(
  api_key=getenv("OPENAI_API_KEY"),
)


class MessageFormatter:
  def __init__(self, system_instruction: str, revise_app_prompt: str):
    self.system_instruction = system_instruction
    self.revise_app_prompt = revise_app_prompt

  def format_messages(
    self, code: str, user_input: str, line_number: int | None
  ) -> list[ChatCompletionMessageParam]:
    # Add sentinel token based on line_number (1-indexed)
    if line_number is not None:
      code_lines = code.splitlines()
      if 1 <= line_number <= len(code_lines):
        code_lines[line_number - 1] += EDIT_HERE_MARKER
      code = "\n".join(code_lines)

    formatted_prompt = self.revise_app_prompt.replace(
      "<APP_CODE>", code
    ).replace("<APP_CHANGES>", user_input)

    return [
      {"role": "system", "content": self.system_instruction},
      {"role": "user", "content": formatted_prompt},
    ]


def MakeDefaultMessageFormatter():
  system_instructions = read_file("src/ai/prompts/mesop_overview.txt")
  base_prompt = read_file("src/ai/prompts/revise_prompt_base.txt")
  prompt = read_file("src/ai/prompts/revise_prompt_shorter.txt")
  return MessageFormatter(system_instructions, base_prompt + "\n\n" + prompt)


def MakeMessageFormatterShorterUserMsg():
  """Formats user messages with a shorter prompt.

  We use a shorter prompt since we will be including goldens that
  have not been fine-tuned yet. This allows us to test new training
  data without having to fine tune all the time.

  Instead the main user instruction prompt will be bundled with user
  instructions instead.
  """
  system_instructions = read_file("src/ai/prompts/mesop_overview.txt")
  revise_instructions = read_file("src/ai/prompts/revise_prompt_base.txt")
  prompt = read_file("src/ai/prompts/revise_prompt_shorter.txt")
  return MessageFormatter(
    system_instructions + "\n\n" + revise_instructions, prompt
  )


def load_unused_goldens():
  goldens_path = "ft/gen/formatted_dataset_for_prompting.jsonl"
  new_goldens = []
  num_rows = 0
  try:
    with open(goldens_path) as f:
      for row in f:
        num_rows += 1
        messages = json.loads(row)["messages"]
        new_goldens.append(messages[1])
        new_goldens.append(messages[2])
    new_goldens.pop(0)  # Remove the redundant system instruction
    print(f"Adding {num_rows} additional examples to prompt.")
  except FileNotFoundError as e:
    print(e)

  return new_goldens


if getenv("MESOP_AI_INCLUDE_NEW_GOLDENS"):
  message_formatter = MakeMessageFormatterShorterUserMsg()
  goldens_path = load_unused_goldens()
else:
  message_formatter = MakeDefaultMessageFormatter()
  goldens_path = []


def format_messages(
  code: str, user_input: str, line_number: int | None
) -> list[ChatCompletionMessageParam]:
  return message_formatter.format_messages(code, user_input, line_number)


def adjust_mesop_app_stream(
  *,
  code: str,
  user_input: str,
  line_number: int | None,
  client: OpenAI = DEFAULT_CLIENT,
  model: str = DEFAULT_MODEL,
):
  """
  Returns a stream of the code diff.
  """
  messages = format_messages(code, user_input, line_number)

  if goldens_path:
    messages = [messages[0], *goldens_path, messages[1]]

  return client.chat.completions.create(
    model=model,
    max_tokens=16_384,
    messages=messages,
    stream=True,
  )


def adjust_mesop_app_blocking(
  *,
  code: str,
  user_input: str,
  line_number: int | None = None,
  client: OpenAI = DEFAULT_CLIENT,
  model: str = DEFAULT_MODEL,
) -> str:
  """
  Returns the code diff.
  """
  messages = format_messages(code, user_input, line_number)
  if goldens_path:
    messages = [messages[0], *goldens_path, messages[1]]

  response = client.chat.completions.create(
    model=model,
    max_tokens=16_384,
    messages=messages,
    stream=False,
  )
  content = response.choices[0].message.content
  assert content is not None
  return content
