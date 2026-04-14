

import numpy as np
from numpy import array
from aspn23 import (
    MeasurementDirection3DToPoints,
    TypeDirection3DToPointReferenceFrame,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeRemotePointPositionReferenceFrame
)

from navtk.navutils import delta_lat_to_north, delta_lon_to_east, quat_to_dcm, skew
from numpy import acos, asin, atan2, cos, eye, float64, sin, zeros
from numpy.linalg import inv, norm
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)

def az_el_to_sin_jac(az: float, el: float)-> NDArray[float64]:
    return array([[cos(el) * cos(az), -sin(az) * sin(el)], [0, -cos(el)]])

def convert_az_el_to_sine_space(x: NDArray[float64], cov: NDArray[float64])->tuple[NDArray[float64], NDArray[float64]]:
    az = x[0]
    el = x[1]
    x1 =-sin(el)
    x0 = sin(az) * cos(el)
    tx = az_el_to_sin_jac(az, el)
    return (array([x0, x1]), tx @ cov @ tx.T)

def convert_sine_space_to_az_el(x: NDArray[float64], cov: NDArray[float64])->tuple[NDArray[float64], NDArray[float64]]:
    el = -asin(x[1])
    az = asin(x[0]/cos(el))
    tx = inv(az_el_to_sin_jac(az, el))
    return (array([az, el]), tx @ cov @ tx.T)

def boresight_xyz_to_az_el(ned: NDArray[float64])->NDArray[float64]:
    r = norm(ned)
    if r < 1e-20:
        return array([0.0, 0.0])
    az = atan2(ned[1], ned[0])
    el = asin(np.dot([0, 0, -1], ned/r))
    return array([az, el])

class DirectionMeasurementProcessor(StandardMeasurementProcessor):
    """
    TODO
    """

    _mediator: Mediator
    _pva: MeasurementPositionVelocityAttitude | None
    _C_platform_to_sensor: NDArray[float64]
    _l_ps_p: NDArray[float64]

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray[float64],
        C_platform_to_sensor: NDArray[float64]
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
        self._C_platform_to_sensor = quat_to_dcm(C_platform_to_sensor)

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
        
        meas = message.wrapped_message

        if self._pva is None or self._pva.time_of_validity.elapsed_nsec != meas.time_of_validity.elapsed_nsec:
            self._mediator.log_message(LoggingLevel.ERROR, "Invalid aux PVA")
            return None
        
        
        # There are multiple formats that the observations can be in. Without a camera model we
        # cannot process REFERENCE_FRAME_PIXEL or REFERENCE_FRAME_NORMALIZED_IMAGE, but 
        # REFERENCE_FRAME_AZ_EL and REFERENCE_FRAME_SINE_SPACE are trivially convertible to one another.
        # The measurement format allows for each observation to have a different reference frame...
        # so we'll need to sweep and harvest only the ones we want.

        keep_obs = []
        keep_cov = []

        if self._pva is None:
            return None
        if self._pva.reference_frame != MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC:
            return None
        if self._pva.p1 is None or self._pva.p2 is None or self._pva.p3 is None:
            return None 

        num_obs = len(meas.obs)
        for k in range(num_obs):
            if meas.obs[k].remote_point.position_reference_frame == TypeRemotePointPositionReferenceFrame.NONE:
                continue
            rp1 = meas.obs[k].remote_point.position1
            rp2 = meas.obs[k].remote_point.position2 
            rp3 = meas.obs[k].remote_point.position3
            
            if rp1 is None or rp2 is None or rp3 is None:
                continue
            
            if meas.obs[k].reference_frame == TypeDirection3DToPointReferenceFrame.AZ_EL:
                keep_obs.append(meas.obs[k].obs)
                keep_cov.append(meas.obs[k].covariance)
            elif meas.obs[k].reference_frame == TypeDirection3DToPointReferenceFrame.SINE_SPACE:
                # convert sine space to az-el
                (azel, azelcov)  = convert_sine_space_to_az_el(meas.obs[k].obs, meas.obs[k].covariance)
                keep_obs.append(azel)
                keep_cov.append(azelcov)
            else:
                continue
        num_obs = len(keep_obs)
        
        # We can pre-allocate our model terms based on the number of observations in the measurement.
        z = np.zeros((2 * num_obs, 1))
        R = np.zeros((2 * num_obs, 2 * num_obs))
        

        for k in range(num_obs):
            z[2 * k:(2 * k + 2), :] = keep_obs[k].reshape((2, 1))
            R[2 * k:(2 * k + 2), 2 * k:(2 * k + 2)] = keep_cov[k]

        def h(x: NDArray[float64]) -> NDArray[float64]:
            out = zeros((2 *num_obs, 1))
            cnp = (eye(3) - skew(x[6:9].flatten())) @ quat_to_dcm(self._pva.quaternion)
            for k in range(num_obs):
                # Find predicted NED coordinates of observation wrt self
                n = delta_lat_to_north(meas.obs[k].remote_point.position1 - self._pva.p1, self._pva.p1, self._pva.p3) - x[0]
                e = delta_lon_to_east(meas.obs[k].remote_point.position2 - self._pva.p2, self._pva.p1, self._pva.p3) - x[1]
                d = self._pva.p3 -  meas.obs[k].remote_point.position3 - x[2]
                ned = array([n, e, d]) - (cnp @ self._l_ps_p).reshape((3, 1))
                # Rotate from ned frame into sensor frame
                xyz = self._C_platform_to_sensor @ cnp.T @ ned
                out[2 * k:(2 * k + 2), :] = boresight_xyz_to_az_el(xyz).reshape((2, 1))
            return out

        H = zeros((2 * num_obs, x_and_p.estimate.shape[0]))

        # Calculate jacobian numerically for now
        for k in range(x_and_p.estimate.shape[0]):
            dx = zeros((x_and_p.estimate.shape[0], 1))
            dx[k] = 1e-6
            jac_col = ((h(dx) - h(-dx))/(2e-6))
            H[:, k] = jac_col.flatten()
        
        return StandardMeasurementModel(z, h, H, R)
