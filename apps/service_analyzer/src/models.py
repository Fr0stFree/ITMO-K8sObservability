import datetime as dt

from google.protobuf.timestamp_pb2 import Timestamp
from pydantic import BaseModel

from protocol.analyzer_pb2 import TargetDetails as TargetDetailsProto, TargetSummary as TargetSummaryProto


class TargetUpdate(BaseModel):
    status: str
    url: str
    checked_at: dt.datetime
    comment: str


class TargetSummary(BaseModel):
    id: str
    url: str
    status: str
    checked_at: dt.datetime
    comment: str
    created_at: dt.datetime

    def to_proto(self) -> TargetSummaryProto:
        checked_at = Timestamp()
        checked_at.FromDatetime(self.checked_at)
        created_at = Timestamp()
        created_at.FromDatetime(self.created_at)
        return TargetSummaryProto(
            id=self.id,
            url=self.url,
            status=self.status,
            checked_at=checked_at,
            comment=self.comment,
            created_at=created_at,
        )


class TargetHistoryItem(BaseModel):
    status: str
    checked_at: dt.datetime
    comment: str

    def to_proto(self) -> TargetDetailsProto.HistoryItem:
        checked_at = Timestamp()
        checked_at.FromDatetime(self.checked_at)
        return TargetDetailsProto.HistoryItem(
            status=self.status,
            checked_at=checked_at,
            comment=self.comment,
        )


class TargetDetails(BaseModel):
    id: str
    url: str
    created_at: dt.datetime
    history: list[TargetHistoryItem]

    def to_proto(self) -> TargetDetailsProto:
        created_at = Timestamp()
        created_at.FromDatetime(self.created_at)
        return TargetDetailsProto(
            id=self.id,
            url=self.url,
            created_at=created_at,
            history=[item.to_proto() for item in self.history],
        )
