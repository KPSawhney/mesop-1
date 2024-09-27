"""Generic helper for constructing actions."""

from typing import AsyncIterable
from genai.content import content_api
from genai.protos import genai_pb2


# TODO(b/369188538): make this a class that supports reading from named IDs.
ActionResponse = AsyncIterable[content_api.Chunk]


class Action:
  """An operation that receives named inputs and returns named outputs.

  It is similar to a function call programming languages.
  """

  name: str
  target_spec: genai_pb2.TargetSpec
  inputs: dict[str, content_api.Content]
  output_names: list[str]

  def __init__(
      self,
      name: str,
      target_id: str,
      inputs: dict[str, content_api.ContentTypes],
      output_names: list[str],
  ):
    """Constructs an action.

    Args:
      name: name of the action to execute.
      target_id: address or identifier of underlying system to run the action
        on.
      inputs: mapping from input name to the input content.
      output_names: names of outputs to return. If empty no outputs will be
        returned at all.
    """
    self.name = name
    self.target_spec = genai_pb2.TargetSpec(id=target_id)
    self.output_names = output_names
    self.inputs = {}
    for param_name, param_val in inputs.items():
      self.inputs[param_name] = content_api.Content(param_val)

  async def run(
      self,
      session: content_api.Session,
  ) -> AsyncIterable[content_api.Chunk]:
    """Writes the action and its content to a Session, closes the session and returns the response.

    Args:
      session: an open session to write the action to.

    Yields:
      response messages from the session.
    """
    # Construct unique IDs for each input parameter.
    ids: dict[str, str] = {
        param_name: content_api.unique_id() for param_name in self.inputs.keys()
    }
    # Construct an action proto given the unique IDs created above.
    action_proto = genai_pb2.Action(
        name=self.name,
        target_spec=self.target_spec,
        inputs=[genai_pb2.NamedParameter(name=p, id=ids[p]) for p in ids],
        outputs=[
            genai_pb2.NamedParameter(name=p, id=content_api.unique_id())
            for p in self.output_names
        ],
    )
    await session.write(action_proto)
    # Write each input parameter to the session.
    for param_name, param_val in self.inputs.items():
      await session.write(param_val, id=ids[param_name])
    # Close session and stream back response.
    await session.done_writing()
    async for chunk in session:
      yield chunk
