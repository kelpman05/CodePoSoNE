import contextvars
import typing


class Metric:
    transport: typing.Dict[str, typing.Any]
    scene: typing.Dict[str, typing.Any]


metric: contextvars.ContextVar[Metric] = contextvars.ContextVar('metric')
