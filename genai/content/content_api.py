"""Simple helpers for dealing with content in Python."""

import functools
from typing import AsyncIterator, Iterable, Iterator, Protocol, Type, TypeVar
import uuid
from genai.protos import genai_pb2
from google.protobuf import message

SessionMessage = genai_pb2.SessionMessage
NodeFragmentProto = genai_pb2.NodeFragment
ProtobufMessageType = TypeVar('ProtobufMessageType', bound=message.Message)


def unique_id() -> str:
    """Returns a globally unique identifier. Can be used to make Node IDs."""
    return uuid.uuid4().hex


def get_proto_message_mimetype(
    message_type: Type[ProtobufMessageType] | ProtobufMessageType,
) -> str:
    """Returns a mimetype associated with the proto 'message_type'."""
    return f'application/x-protobuf; type={message_type.DESCRIPTOR.full_name}'


class ChunkMetadata:
    """Convenience wrapper for ChunkMetadata proto."""

    proto: genai_pb2.ChunkMetadata

    def __init__(self, value=None, **kwargs):
        if value is None:
            self.proto = genai_pb2.ChunkMetadata()
        elif isinstance(value, ChunkMetadata):
            self.proto = value.proto
        elif isinstance(value, genai_pb2.ChunkMetadata):
            self.proto = value
        else:
            raise ValueError(f'Invalid mimetype type: {type(value)}')
        self.proto.MergeFrom(genai_pb2.ChunkMetadata(**kwargs))

    @property
    def mimetype(self) -> str:
        return self.proto.mimetype

    @mimetype.setter
    def mimetype(self, mime: str) -> None:
        self.proto.mimetype = mime

    @property
    def role(self) -> str:
        return self.proto.role

    @role.setter
    def role(self, role_str: str) -> None:
        self.proto.role = role_str

    def __repr__(self) -> str:
        return str(self.proto)

    def __eq__(self, other: 'ChunkMetadata') -> bool:
        return self.proto == other.proto


ChunkMetadataTypes = ChunkMetadata | genai_pb2.ChunkMetadata


class Chunk:
    """Convenience wrapper for genai_pb2.Chunk."""

    proto: genai_pb2.Chunk
    _chunk_id: str

    def __init__(
        self,
        value,
        *,
        metadata: ChunkMetadataTypes | None = None,
        id: str | None = None,  # pylint: disable=redefined-builtin
    ):
        if isinstance(value, str):
            self.proto = genai_pb2.Chunk(
                metadata=ChunkMetadata(mimetype='text/plain').proto,
                data=bytes(value, 'utf-8'),
            )
        elif isinstance(value, Chunk):
            self.proto = value.proto
            id = value.id
        elif isinstance(value, genai_pb2.Chunk):
            self.proto = value
        elif isinstance(value, bytes):
            self.proto = genai_pb2.Chunk(data=value)
            if metadata is None or not metadata.mimetype:
                raise ValueError(
                    'When providing bytes as the chunk value, you must specify the '
                    'mimetype.'
                )
        elif isinstance(value, message.Message):
            self.proto = genai_pb2.Chunk(
                metadata=genai_pb2.ChunkMetadata(
                    mimetype=get_proto_message_mimetype(value),
                ),
                data=value.SerializeToString(),
            )
        else:
            raise ValueError(f'Invalid chunk type: {type(value)}')
        if metadata:
            self.proto.metadata.MergeFrom(ChunkMetadata(metadata).proto)
        self._chunk_id = id or unique_id()

    def as_text(self, raise_on_error: bool = True) -> str:
        """Converts the chunk to a text string if possible.

        Args:
          raise_on_error: whether to raise an error if the chunk payload does not
            contain text.

        Returns:
          A text string, if the chunk payload contains text.
        """
        if not self.proto.data:  # Ignore empty chunks.
            return ''
        mimetype = self.metadata.mimetype
        if not mimetype.startswith('text/') and not mimetype.endswith('/url'):
            if raise_on_error:
                raise ValueError(
                    f'Cannot convert chunk of type {mimetype} to text.')
            else:
                return ''
        return self.proto.data.decode()

    def as_proto_message(
        self, message_type: Type[ProtobufMessageType]
    ) -> ProtobufMessageType:
        """Returns a decoded protobuf message from the chunk.

        Example usage:
          proto_message = chunk.as_proto_message(struct_pb2.Struct)

        Args:
          message_type: The message type to decode.

        Returns:
          A decoded protobuf message of the given type.

        Raises:
          ValueError: If the chunk's mimetype does not match the provided message
          type.
        """
        if self.proto.metadata.mimetype != get_proto_message_mimetype(message_type):
            raise ValueError(
                'Mismatching protobuf message mimetype.'
                f' Expected={get_proto_message_mimetype(message_type)},'
                f' Got={self.proto.metadata.mimetype}.'
            )

        proto = message_type()
        proto.ParseFromString(self.proto.data)
        return proto

    @property
    def metadata(self) -> ChunkMetadata:
        """Convenience helper for getting the metadata attached to the chunk."""
        return ChunkMetadata(self.proto.metadata)

    @property
    def id(self) -> str:
        return self._chunk_id

    def __repr__(self) -> str:
        return f'id: {self.id}\n{str(self.proto)}'

    def __eq__(self, other) -> bool:
        return self.proto == other.proto and self.id == other.id


class Content:
    """Convenience wrapper for a sequence of chunks."""

    id: str
    _chunks: list[Chunk]

    def __init__(self, *chunks: 'ContentTypes', id: str | None = None):  # pylint: disable=redefined-builtin
        if len(chunks) == 1 and isinstance(chunks[0], Content):
            self._chunks = chunks[0]._chunks
            id = id or chunks[0].id
        else:
            self._chunks = []
            for chunk in chunks:
                self += chunk
        self.id = id or unique_id()

    def __iadd__(self, other: 'ContentTypes') -> 'Content':
        """Appends other to the content."""
        if isinstance(other, Content):
            self += other._chunks
        elif isinstance(other, ChunkTypes):
            self._chunks.append(Chunk(other))
        elif isinstance(other, Iterable):
            for chunk in other:
                self += chunk
        else:
            raise ValueError(f"Can't append {type(other)} to Content.")
        return self

    def __add__(self, other: 'ContentTypes') -> 'Content':
        """Returns concatenation of two contents."""
        result = Content()
        result += self
        result += other
        result.id = self.id
        return result

    @property
    def node_fragments(self) -> Iterable[NodeFragmentProto]:
        """Yields the chunks as NodeFragments and a root fragment with the given ID."""
        root = NodeFragmentProto(id=self.id)
        for chunk in self._chunks:
            chunk_id = unique_id()
            yield NodeFragmentProto(chunk_fragment=chunk.proto, id=chunk_id)
            root.child_ids.append(chunk_id)
        yield root

    def as_text(self, raise_on_error: bool = True) -> str:
        """Converts the chunk to a text string if possible.

        Args:
          raise_on_error: whether to raise an error if the chunk payload does not
            contain text.

        Returns:
          A text string, if the chunk payload contains text.
        """
        text = ''
        for chunk in self._chunks:
            text += chunk.as_text(raise_on_error)
        return text

    def __iter__(self) -> Iterator[Chunk]:
        """Iterates through the chunks of the content."""
        for chunk in self._chunks:
            yield chunk

    def __repr__(self) -> str:
        return f'id: {self.id}\n\n' + '\n'.join([str(c) for c in self._chunks])

    def __eq__(self, other) -> bool:
        if len(self) != len(other) or self.id != other.id:
            return False
        for c1, c2 in zip(self._chunks, list(other)):
            if c1 != c2:
                return False
        return True

    def __len__(self) -> int:
        return len(self._chunks)


# Types that can be converted to Chunk.
ChunkTypes = str | bytes | Chunk | genai_pb2.Chunk | message.Message

ContentTypes = Content | ChunkTypes | Iterable[ChunkTypes]

# Types that can be written to a BidiStream.
StreamWritable = (
    ContentTypes | NodeFragmentProto | SessionMessage | genai_pb2.Action
)


class BidiStream(Protocol):

    def __aiter__(self) -> AsyncIterator[SessionMessage]:
        pass

    async def write(self, request: SessionMessage) -> None:
        pass

    async def done_writing(self) -> None:
        pass


class Session:
    """Convenience wrapper for the BidiStream of SessionMessages."""
    # TODO(b/369189321): Make Session a context manager.

    _stream: BidiStream

    def __init__(self, stream: BidiStream):
        self._stream = stream

    async def write(
        self,
        value: StreamWritable,
        id: str | None = None,  # pylint: disable=redefined-builtin
    ) -> None:
        """Writes a message to the stream.

        Args:
          value: something to write to the stream, can be a direct SessionMessage or
            NodeFragment proto, or convertible to Chunk objects.
          id: optional ID to assign to the root NodeFragment.
        """
        writable = None
        if isinstance(value, SessionMessage):
            if id is not None:
                raise ValueError(
                    'You cannot provide an ID alongside a SessionMessage.')
            writable = value
        elif isinstance(value, genai_pb2.NodeFragment):
            if id is not None:
                value.id = id
            writable = SessionMessage(node_fragments=[value])
        elif isinstance(value, genai_pb2.Action):
            writable = SessionMessage(actions=[value])
        else:  # Value should be convertible to Content.
            node_fragments = Content(value, id=id).node_fragments
            writable = SessionMessage(node_fragments=node_fragments)
        await self._stream.write(writable)

    async def __aiter__(self) -> AsyncIterator[Chunk]:
        """Reads chunks from the stream.

        Yields:
          Chunks constructed from ChunkFragments read from the stream.
        """
        async for response in self._stream:
            for node_fragment in response.node_fragments:
                if node_fragment.HasField('chunk_fragment'):
                    yield Chunk(node_fragment.chunk_fragment)

    async def done_writing(self) -> None:
        await self._stream.done_writing()


def _chunk_with_role(
    value,
    *,
    role: str,
    metadata: ChunkMetadataTypes | None = None,
    id: str | None = None,  # pylint: disable=redefined-builtin
) -> Chunk:
    return Chunk(value, id=id, metadata=ChunkMetadata(metadata, role=role))


user_chunk = functools.partial(_chunk_with_role, role='USER')
assistant_chunk = functools.partial(_chunk_with_role, role='ASSISTANT')
system_chunk = functools.partial(_chunk_with_role, role='SYSTEM')
