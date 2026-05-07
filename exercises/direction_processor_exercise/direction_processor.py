from numpy import float64, zeros
from numpy.typing import NDArray
from pntos.api import (
    GenXandP,
    Mediator,
    Message,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)


class DirectionMeasurementProcessor(StandardMeasurementProcessor):
    _mediator: Mediator

    def __init__(
        self, label: str, state_block_labels: list[str], mediator: Mediator
    ) -> None:
        raise NotImplementedError(
            'DirectionProcessor needs initialized. Additional parameters from the plugin/config may be required.'
        )

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        raise NotImplementedError(
            'The DirectionProcessor may need to accept some aux data.'
        )

    def generate_model(
        self,
        message: Message,
        x_and_p: GenXandP,
    ) -> StandardMeasurementModel | None:
        num_states = 0  # Expected size of state vector
        size_of_obs = 0  # Expected size of a single feature observation vector
        number_of_obs = 0  # Number of observations included in message- it may vary
        m = size_of_obs * number_of_obs

        # Dummy containers to demonstrate expected shapes
        z = zeros((m, 1))
        R = zeros((m, m))
        H = zeros((m, num_states))

        def h(x: NDArray[float64]) -> NDArray[float64]:
            raise NotImplementedError(
                'Must implement the non-linear measurement function.'
            )
            # return zeros((m, 1))

        return StandardMeasurementModel(z, h, H, R)
