import datetime as dt

from google.protobuf.timestamp_pb2 import Timestamp
from pydantic import BaseModel

from protocol.analyzer_pb2 import Target as TargetProto


class BaseTarget(BaseModel):
    status: str
    url: str
    checked_at: dt.datetime
    comment: str


class TargetUpdate(BaseTarget):
    pass


class Target(BaseTarget):
    id: str

    def to_proto(self) -> TargetProto:
        timestamp = Timestamp()
        timestamp.FromDatetime(self.checked_at)
        return TargetProto(
            id=self.id,
            url=self.url,
            status=self.status,
            checked_at=timestamp,
        )
