from aspn23 import (
    AspnBase,
    MeasurementVelocity,
    MeasurementVelocityErrorModel,
    MeasurementVelocityReferenceFrame,
)
from pntos.api import (
    Mediator,
    Message,
    Preprocessor,
)
from numpy.typing import NDArray
from numpy import float64, array, eye


class ZuptPreprocessor(Preprocessor):
    _mediator: Mediator
    _output_identifier: str
    _times: list[list[int]]
    _last_zupt: int | None
    _t0: int | None

    def __init__(self, mediator: Mediator, stationary_times: NDArray[float64]) -> None:
        self._mediator = mediator
        self._output_identifier = '/preproc/simulated/zupt'
        stationary_times = array(stationary_times, dtype=int) * 1e9
        self._times = stationary_times.tolist()
        self._last_zupt = None
        self._t0 = None

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        msg = message.wrapped_message
        abs_time = msg.time_of_validity.elapsed_nsec  # type: ignore[attr-defined]
        if self._t0 is None:
            self._t0 = abs_time
        rel_time = msg.time_of_validity.elapsed_nsec - self._t0  # type: ignore[attr-defined]
        for time_range in self._times:
            if rel_time >= time_range[0] and rel_time <= time_range[1]:
                if self._last_zupt is None:
                    self._last_zupt = rel_time
                    return [message, self._produce_zupt(msg)]
                if (rel_time - self._last_zupt) < 1e9:
                    return [message]
                self._last_zupt = rel_time
                return [message, self._produce_zupt(msg)]
        return [message]

    def _produce_zupt(self, msg: AspnBase) -> Message:
        return Message(
            MeasurementVelocity(
                msg.header,  # type: ignore[attr-defined]
                msg.time_of_validity,  # type: ignore[attr-defined]
                MeasurementVelocityReferenceFrame.NED,
                0,
                0,
                0,
                eye(3) * 1e-4,
                MeasurementVelocityErrorModel.NONE,
                array(None),
                [],
            ),
            source_identifier=self._output_identifier,
        )
