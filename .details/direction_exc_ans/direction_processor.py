from aspn23 import (
    MeasurementDirection3DToPoints,
    TypeDirection3DToPointReferenceFrame,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeRemotePointPositionReferenceFrame,
)

from navtk.navutils import delta_lat_to_north, delta_lon_to_east, quat_to_dcm, skew
from numpy import asin, atan2, cos, eye, float64, sin, zeros, asarray, array, copy, dot
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


def az_el_to_sin_jac(az: float, el: float) -> NDArray[float64]:
    """
    Jacobian of the azimuth/elevation to sine space-transform.

    Used to convert an azimuth/elevation covariance into sine-space,
    or vice-versa using the inverse.

    Args:
        az: Azimuth, radians
        el: Elevation, radians
    Return:
        2x2 jacobian matrix.
    """
    return array([[cos(el) * cos(az), -sin(az) * sin(el)], [0, -cos(el)]])


def convert_sine_space_to_az_el(
    x: NDArray[float64], cov: NDArray[float64]
) -> tuple[NDArray[float64], NDArray[float64]]:
    """
    Converts a sine-space direction to azimuth/elevation.

    Args:
        x: 2 element vector containing sine-space measurements.
        cov: 2x2 covariance matrix, units matching x.
    Return:
        2-tuple containing converted estimate and covariance.
    """
    el = -asin(x[1])
    az = asin(x[0] / cos(el))
    tx = inv(az_el_to_sin_jac(az, el))
    return (array([az, el]), tx @ cov @ tx.T)


def boresight_xyz_to_az_el(dp: NDArray[float64]) -> NDArray[float64]:
    """
    Converts a position vector in the sensor frame to an azimuth and elevation.

    Args:
        dp: 3-element position vector originating at the sensor frame origin to some feature,
            in the sensor frame.
    Return:
        2-vector azimuth and elevation relative to the sensor frame (forward-right-down), in radians.
        Azimuth is measured from the sensor x axis and is a positive right-hand rotation about
        sensor z-axis (toward the sensor y-axis). Elevation measures negative from the sensor
        x-y plane towards z (e.g. a point in the x-y plane has 0 elevation, and a point 'above'
        the x-y plane has a positive elevation).
    """
    r = norm(dp)
    if r < 1e-20:
        return array([0.0, 0.0])
    az = atan2(dp[1], dp[0])
    el = asin(dot([0, 0, -1], dp / r))
    return array([az, el])


class DirectionMeasurementProcessor(StandardMeasurementProcessor):
    """
    MeasurementProcessor that uses MeasurementDirection3DToPoints to update pinson-style error states.
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
        C_platform_to_sensor: NDArray[float64],
    ) -> None:
        """
        Initialize the MeasurementProcessor.

        Args:
           label: Identifier for this processor.
           state_block_labels: List of state blocks this processor will generate a measurement model
               against. The first entry must refer to a 'pinson'-style state block with NED frame
               position errors in meters as the first 3 states and NED frame tilt errors in radians
               in locations [6:9].
            mediator: Mediator instance, used for logging.
            l_ps_p: 3-element lever arm from the platform to the sensor in the platform frame, meters.
            C_platform_to_sensor: DCM that rotates a vector from the platform to sensor frame, i.e. sensor
                mounting orientation.
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
        self._C_platform_to_sensor = quat_to_dcm(asarray(C_platform_to_sensor))

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        """
        Stores auxiliary data.

        Only keeps the most recently provided MeasurementPositionVelocityAttitude for use as a nominal
        PVA/linearization point. Measurements should be 'uncorrected' e.g. free inertial since the
        last time state feedback was applied.

        PVA reference frame must be MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC.

        Args:
            aux: List of potential aux data.
        """
        for m in aux:
            if (
                m
                and isinstance(m.wrapped_message, MeasurementPositionVelocityAttitude)
                and m.wrapped_message.reference_frame
                == MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC
            ):
                self._pva = m.wrapped_message

    def generate_model(
        self,
        message: Message,
        x_and_p: EstimateWithCovariance,
    ) -> StandardMeasurementModel | None:
        """
        Generates a StandardMeasurementModel.

        Expects MeasurementDirection3DToPoints as the measurement. Given the current aux data and a
        measurement, generates a measurement model that relates azimuth/elevation measurements in
        radians to 'pinson' style position, velocity and attitude errors, as specified in the Cobra
        pinson15 block.

        Args:
            message: Message, ideally containing MeasurementDirection3DToPoints. Only observations
            tagged as TypeDirection3DToPointReferenceFrame.SINE_SPACE or
            TypeDirection3DToPointReferenceFrame.AZ_EL are supported.
            x_and_p: 15-element EstimateWithCovariance with the current state of the Pinson15 state
                block this processor is related to by state_block_labels.

        Return:
            MeasurementModel relating all observations in message to the pinson states. No model
            will be returned if:
            - No PVA aux data has been received.
            - PVA aux data time doesn't match time stored in message.
            - PVA aux data is missing any position members or the attitude quaternion.
            - All feature positions in message observations are missing one or more positon element.
            - message
        """
        # Verify measurement is of correct type and return None if not
        if not isinstance(message.wrapped_message, MeasurementDirection3DToPoints):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'DirectionMeasurementProcessor expected message of type MeasurementDirection3DToPoints, \
                    but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        meas = message.wrapped_message

        # Verify aux PVA exists, is at the correct time, and has valid position data.
        if (
            self._pva is None
            or self._pva.time_of_validity.elapsed_nsec
            != meas.time_of_validity.elapsed_nsec
        ):
            self._mediator.log_message(LoggingLevel.ERROR, 'Invalid aux PVA')
            return None

        if self._pva.p1 is None or self._pva.p2 is None or self._pva.p3 is None:
            return None

        # There are multiple formats that the observations can be in. Without a camera model we
        # cannot process REFERENCE_FRAME_PIXEL or REFERENCE_FRAME_NORMALIZED_IMAGE, but
        # REFERENCE_FRAME_AZ_EL and REFERENCE_FRAME_SINE_SPACE are trivially convertible to one another.
        # The measurement format allows for each individual observation to have a different reference
        # frame, so we need to sweep and harvest only the ones we can use.
        keep_obs = []
        keep_cov = []

        num_obs = len(meas.obs)
        for k in range(num_obs):
            # Ignore features of unknown frame, or insufficiently specified.
            if (
                meas.obs[k].remote_point.position_reference_frame
                == TypeRemotePointPositionReferenceFrame.NONE
            ):
                continue
            rp1 = meas.obs[k].remote_point.position1
            rp2 = meas.obs[k].remote_point.position2
            rp3 = meas.obs[k].remote_point.position3

            if rp1 is None or rp2 is None or rp3 is None:
                continue

            # Convert measurements we can use to azimuth/elevation format.
            if (
                meas.obs[k].reference_frame
                == TypeDirection3DToPointReferenceFrame.AZ_EL
            ):
                keep_obs.append(meas.obs[k].obs)
                keep_cov.append(meas.obs[k].covariance)
            elif (
                meas.obs[k].reference_frame
                == TypeDirection3DToPointReferenceFrame.SINE_SPACE
            ):
                # convert sine space to az-el
                (azel, azelcov) = convert_sine_space_to_az_el(
                    meas.obs[k].obs, meas.obs[k].covariance
                )
                keep_obs.append(azel)
                keep_cov.append(azelcov)
            else:
                continue

        # Reset to account for measurements we rejected
        num_obs = len(keep_obs)

        if num_obs < 1:
            return None

        # We can pre-allocate our model terms based on the number of observations in the measurement.
        z = zeros((2 * num_obs, 1))
        R = zeros((2 * num_obs, 2 * num_obs))

        # Assign each measurement and covariance sequentially into model params
        for k in range(num_obs):
            z[2 * k : (2 * k + 2), :] = keep_obs[k].reshape((2, 1))
            R[2 * k : (2 * k + 2), 2 * k : (2 * k + 2)] = keep_cov[k]

        def calculate_boresight_arg(
            x: NDArray[float64],
            cnp: NDArray[float64],
            rp: NDArray[float64],
            pva: NDArray[float64],
        ) -> NDArray[float64]:
            # Find predicted NED coordinates of observation wrt self, correcting the nominal
            # with the error states
            n = delta_lat_to_north(rp[0] - pva[0], pva[0], pva[2]) - x[0]
            e = delta_lon_to_east(rp[1] - pva[1], pva[0], pva[2]) - x[1]
            d = pva[2] - rp[2] - x[2]
            # Subtract off the lever arm in the NED frame to get the vector from the
            # sensor to the observation location
            ned = array([n, e, d]) - (cnp @ self._l_ps_p).reshape((3, 1))
            # Rotate from ned frame into sensor frame i.e. boresight
            return self._C_platform_to_sensor @ cnp.T @ ned

        # Define the non-linear measurement function that predicts the azimuth and elevation
        # of each observed feature given nominal observer position, the feature position, the
        # error state estimates, and the lever arm and rotation from the platform to the
        # sensor that made the observations.
        def h(x: NDArray[float64]) -> NDArray[float64]:
            # All of these were checked earlier, but typechecking insists it be done again.
            # Since we know these are safe, just use asserts.
            assert self._pva is not None
            assert self._pva.quaternion is not None
            assert self._pva.p1 is not None
            assert self._pva.p2 is not None
            assert self._pva.p3 is not None
            pva = array([self._pva.p1, self._pva.p2, self._pva.p3])
            # First-order correction of the nominal platform to NED rotation with current tilt
            # error estimates
            cnp = (eye(3) - skew(x[6:9].flatten())) @ quat_to_dcm(self._pva.quaternion)

            out = zeros((2 * num_obs, 1))
            for k in range(num_obs):
                rp = meas.obs[k].remote_point
                assert rp.position1 is not None
                assert rp.position2 is not None
                assert rp.position3 is not None
                feature_pos = array([rp.position1, rp.position2, rp.position3])

                xyz = calculate_boresight_arg(x, cnp, feature_pos, pva)
                # Convert the position vector to an azimuth/elevation and assign
                out[2 * k : (2 * k + 2), :] = boresight_xyz_to_az_el(xyz).reshape(
                    (2, 1)
                )
            # Return all predicted azimuth/elevation measurements
            return out

        # Using x_and_p.estimate.shape is preferred to hardcoding a state block size as it allows
        # all state blocks that contain the required states in the correct locations (in this case
        # position errors in [0:3] and attitude errors in [6:9]) to be used with the same processor.
        H = zeros((2 * num_obs, x_and_p.estimate.shape[0]))

        # The non-linear measurement function is fairly involved, one way to get the jacobian is
        # numerically
        delta = 1e-6
        for k in range(x_and_p.estimate.shape[0]):
            dx_high = copy(x_and_p.estimate)
            dx_low = copy(x_and_p.estimate)
            dx_high[k] += delta
            dx_low[k] -= delta
            jac_col = (h(dx_high) - h(dx_low)) / (2 * delta)
            H[:, k] = jac_col.flatten()

        return StandardMeasurementModel(z, h, H, R)
