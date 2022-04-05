from datetime import datetime
import typing


class TimestampMixin:
    timestamp_fields: typing.List[str] = []

    def register_timestamp(self, *fields, reset=False):
        if reset:
            self.timestamp_fields = []
        self.timestamp_fields.extend(fields)

    @property
    def timestamps(self):
        ans = {}
        for field in self.timestamp_fields:
            t = getattr(self, field)
            if isinstance(t, datetime):
                ans[field] = t.timestamp()
        return ans
