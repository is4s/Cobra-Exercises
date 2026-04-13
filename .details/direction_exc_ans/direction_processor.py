import array

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
from numpy import asin, cos, float64, sin
from numpy.linalg import inv
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
        calc_az_el = []
        keep_cov = []

        if self._pva is None:
            return None
        if self._pva.reference_frame != MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC:
            return None
        if self._pva.p1 is None or self._pva.p2 is None or self._pva.p3 is None:
            return None 
        self_llh = [self._pva.p1, self._pva.p2, self._pva.p3]
        self_ecef = llh_to_ecef(self_llh)

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
            obs_ecef = llh_to_ecef([rp1, rp2, rp3])
            #calc_az_el.append([calc_sv_azimuth(self_ecef, obs_ecef), calc_sv_elevation(self._pva.p1, self._pva.p2, self_ecef, obs_ecef)])
            vec_ecef = obs_ecef - self_ecef
            unit_vec_ecef = vec_ecef/np.linalg.norm(vec_ecef)
            cen = llh_to_cen(self_llh)
            unit_vec_ned = cen.T @ unit_vec_ecef
            cnp = quat_to_dcm(self._pva.quaternion)
            unit_vec_platform = cnp.T @ unit_vec_ned
            unit_vec_sensor = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]) @ (unit_vec_platform + self._l_ps_p)
            az = np.arctan2(unit_vec_sensor[1], unit_vec_sensor[0])
            el =  np.asin(np.dot([0, 0, -1], unit_vec_sensor))
            calc_az_el.append([az, el])
            print("Measurement comparison")
            print(f"SV version {calc_az_el[-1]}")
            print(f"Meas {keep_obs[-1]}\n")
            print(keep_obs[-1][0] + calc_az_el[-1][0])

        num_obs = len(keep_obs)
        
        # We can pre-allocate our model terms based on the number of observations in the measurement.
        z = np.zeros((2 * num_obs, 1))
        R = np.zeros((2 * num_obs, 2 * num_obs))
        H = np.zeros((2 * num_obs, x_and_p.estimate.shape[0]))

        for k in range(num_obs):
            z[k:k+2, :] = keep_obs[k].reshape((2, 1))
            R[k:k+2, k:k+2] = keep_cov[k]

        def h(x: NDArray[float64]) -> NDArray[float64]:
            # TODO
            return z
        
        return StandardMeasurementModel(z, h, H, R)
