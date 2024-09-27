"""Client for the GENERATE action."""

from genai.content import content_api
from genai.actions import action_base


class Generate(action_base.Action):
  """Generate helps writing a generate action to a session."""

  def __init__(
      self,
      prompt: content_api.ContentTypes,
      *,
      target_id: str,
  ):
    super().__init__(
        name='GENERATE',
        target_id=target_id,
        inputs={'prompt': prompt},
        output_names=['response'],
    )


def debug_format_text(content: content_api.Content) -> str:
  """Prints text-only content formatted with roles. For debugging only."""
  debug_str = ''
  last_role = 'USER'  # Unset initial role sent to server defaults to USER.
  rolling_message = ''
  for chunk in content:
    if not chunk.metadata.role or chunk.metadata.role == last_role:
      rolling_message += chunk.as_text()
    else:
      if rolling_message:
        debug_str += f'{last_role}: {rolling_message}\n'
      rolling_message = chunk.as_text()
      last_role = chunk.metadata.role
  if rolling_message:
    debug_str += f'{last_role}: {rolling_message}'
  return debug_str
