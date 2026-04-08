from aspn23 import (
    MeasurementVelocity,  # noqa: F401
)
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)


class ZuptPreprocessor(Preprocessor):
    _mediator: Mediator

    def __init__(
        self,
        mediator: Mediator,
    ) -> None:
        self._mediator = mediator
        # Edit me!
        # NOTE: I am the constructor so I am only called once!

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        # Implement Me!

        # REMOVE THE MESSAGE BELOW AFTER IMPLEMENTING
        self._mediator.log_message(
            LoggingLevel.WARN,
            'ZuptPreprocessor.process_pntos_message has not been' + ' implemented yet.',
        )
        return None
