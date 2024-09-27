"""Python client for using the API."""

import enum
from genai.content import content_api
from genai.actions import action_base
import grpc


@enum.unique
class Endpoint(enum.Enum):
  GEMINI_API = enum.auto()
  GDM_API = enum.auto()
  CUSTOM_API = enum.auto()


def _address_and_method(
    endpoint: Endpoint,
    host: str | None = None,
) -> tuple[str, str]:
  """Fetches the service URL and method for the provided endpoint type."""
  if endpoint == Endpoint.GEMINI_API:
    return (
        'generativelanguage.googleapis.com',
        '/google.ai.generativelanguage.v1alpha.EvergreenService/StartSession',
    )
  elif Endpoint.GDM_API:
    return (
        'dns:///gdmlabs.googleapis.com:443',
        '/evergreen.v2.EvergreenService/StartSession',
    )
  elif Endpoint.CUSTOM_API:
    if host is None:
      raise ValueError('Host must be specified when using a custom backend.')
    return (host, '/evergreen.v2.EvergreenService/StartSession')
  else:
    raise ValueError(f'Invalid endpoint {endpoint}.')


class Client:
  """Client for accessing the API."""

  def __init__(
      self,
      api_key: str,
      *,
      endpoint: Endpoint = Endpoint.GEMINI_API,
      host: str | None = None,
  ):
    self._address, self._method = _address_and_method(endpoint, host)
    self._creds = grpc.ssl_channel_credentials()
    self._metadata = [('x-goog-api-key', api_key)]

  async def start_session(self) -> content_api.Session:
    """Starts a stream.

    Returns:
      An Stream wrapper.
    """
    channel = grpc.aio.secure_channel(self._address, self._creds)
    stream = channel.stream_stream(
        self._method,
        request_serializer=content_api.SessionMessage.SerializeToString,
        response_deserializer=content_api.SessionMessage.FromString,
    )(metadata=self._metadata)
    return content_api.Session(stream)

  async def run(
      self,
      action: action_base.Action,
  ) -> action_base.ActionResponse:
    """Opens a session, runs an action, and closes the session again."""
    session = await self.start_session()
    async for chunk in action.run(session):
      yield chunk
