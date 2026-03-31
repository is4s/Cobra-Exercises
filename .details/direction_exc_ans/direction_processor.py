import numpy as np
from aspn23 import (
    MeasurementDirection3DToPoints,
    TypeDirection3DToPointReferenceFrame,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeRemotePointPositionReferenceFrame
)

from navtk.gnssutils import calc_sv_azimuth, calc_sv_elevation
from navtk.navutils import llh_to_ecef, llh_to_cen, quat_to_dcm
from numpy import asin, cos, float64
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)

class DirectionMeasurementProcessor(StandardMeasurementProcessor):
    """
    TODO
    """

    _mediator: Mediator
    _pva: MeasurementPositionVelocityAttitude | None

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray[float64],
    ) -> None:
        """
        TODO
        """
        if len(state_block_labels) != 1:  # noqa: PLR2004
            mediator.log_message(
                LoggingLevel.ERROR,
                f'DirectionMeasurementProcessor expects one state block label but received {len(state_block_labels)}.',
            )
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._l_ps_p = l_ps_p
        self._pva = None

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        # Just keep the latest aux
        for m in aux:
            if isinstance(m.wrapped_message, MeasurementPositionVelocityAttitude):
                self._pva = m.wrapped_message

    def generate_model(
        self,
        message: Message,
        x_and_p: EstimateWithCovariance,
    ) -> StandardMeasurementModel | None:
        """
        TODO
        """
        if not isinstance(message.wrapped_message, MeasurementDirection3DToPoints):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'DirectionMeasurementProcessor expected message of type MeasurementDirection3DToPoints, \
                    but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None
        
        # Make sure that the state block label(s) that we are generating a model against
        # exist and have an estimate/covariance in the filter.
        ewc = gen_x_and_p_func(self.state_block_labels)
        if ewc is None:
            return None
        
        meas = message.wrapped_message
        # There are multiple formats that the observations can be in. Without a camera model we
        # cannot process REFERENCE_FRAME_PIXEL or REFERENCE_FRAME_NORMALIZED_IMAGE, but 
        # REFERENCE_FRAME_AZ_EL and REFERENCE_FRAME_SINE_SPACE are trivially convertible to one another.
        # The measurement format allows for each observation to have a different reference frame...
        # so we'll need to sweep and harvest only the ones we want.

        
        # We can pre-allocate our model terms based on the number of observations in the measurement.
        
        num_obs = len(meas.obs)
        z = np.zeros((2 * num_obs, 1))
        R = np.zeros((2 * num_obs, 2 * num_obs))
        H = np.zeros((2 * num_obs, ewc.estimate.shape[0]))

        for k in range(num_obs):
            z[:, k] = meas.obs[k].obs
            R[k:k+2, k:k+2] = meas.obs[k].covariance

        def h(x: NDArray[float64]) -> NDArray[float64]:
            # TODO
            return x
        
        return StandardMeasurementModel(z, h, H, R)
