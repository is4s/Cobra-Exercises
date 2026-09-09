# Exercise 3: Add a Direction to Known Feature Processor

In this exercise, you are tasked with adding a new processor with a more complicated measurement
model. Throughout this exercise, you will learn how to write and utilize a measurement processor in
`pntos-python`. All of the files in `exercises/direction_exercise` will need to be modified in order
to fully implement the processor. To complete the exercise, write the new measurement processor and
modify the stubbed-out app to use the new processor.

## Motivation

Many of the measurement processors in `cobra` and features added in prior exercises are pretty basic
from a sensor modeling standpoint. Most incorporate a direct measurement of some platform parameter,
such as position or velocity. This exercise guides you through adding a new processor that
ingests an *indirect* measurement—the polar angles to features, such as might be extracted from
camera images. The measurement model is quite non-linear, and the number of observations per update
can vary.

## Dataset

The [datafile](https://is4s.github.io/Cobra/example_data.html) used for this example is
the same as in the prior exercises. We'll be using the **/sensor/simulated/directiontoknownfeature**
channel.

One critical piece of information is that the sensor measurements are in a downward-looking sensor frame.
Use `(0.707106781, 0.0, 0.707106781, 0.0)` for the sensor to platform quaternion and `(0.80, 0.0, 0.05)`
for the lever arm in the sensor config.

## Verifying Solution

Since there is no one "right" way to write it, there is also no one "right" way to judge it either.
Instead, we have provided the results from a nominal solution that our own engineers wrote below. Feel
free to compare our results to yours to see how they match up!

```{image} images/direction_NED_Pos_Error.png
:width: 1000px
```

```{image} images/direction_NED_Vel_Error.png
:width: 1000px
```

```{image} images/direction_NED_Tilt_Error.png
:width: 1000px
```

## Helpful Tips

```{dropdown} I don't understand how to start solving the problem.
We recommend starting with the easy parts—the app and the sensor plugin. If you completed the ZUPT
exercise, the process for these two pieces will be quite similar. Try and set up the app to generate
a processor that does nothing first, and then fill in the math in the processor later.
```

```{dropdown} I have the new processor, but I'm not sure how to implement the model.
- The heart of a StandardMeasurementModel is the nonlinear measurement function h(). This function
takes a state vector and produces *predicted* measurements. In order to do this, you need to
understand the states you are bringing in, and the contents of the measurements.
Have a look at the documentation for the [the python measurement class](https://github.com/is4s/aspn-generated/blob/main/aspn-py/src/aspn23/measurement_direction_3d_to_points.py). Notice that the actual observations are a
list of a [nested types](https://github.com/is4s/aspn-generated/blob/main/aspn-py/src/aspn23/type_direction_3d_to_point.py).
You'll need to pay attention what `reference_frame` you are dealing with.

- If you are using the 'pinson' state block as in the other exercises, your processor *will* need
to ingest nominal inertial PVA data.

- It is also worth mentioning that you have some leeway in what the measurement vector z contains—you
do not necessarily need to use the raw measurement observations in their original format.

- Finally, this model will probably require a fair number of conversions. The `navtk.navutils` module
  has a number of functions that may be useful; `delta_lat_to_north`, `delta_lon_to_east`,
  `quat_to_dcm`, and `skew ` form a non-exhaustive set of likely candidates.

```

````{dropdown} These measurement units are unfamiliar.
If you've gotten to the point where you are parsing the input message but are unfamiliar with
what SINE_SPACE is, you can relate sine-space to azimuth-elevation representation using this function:

```python
def convert_sine_space_to_az_el(x: NDArray[float64]) -> NDArray[float64]:
    """
    Converts a sine-space direction to azimuth/elevation.

    Args:
        x: 2 element vector containing sine-space measurements.
    Return:
        2-vector of azimuth and elevation, radians.
    """
    el = -asin(x[1])
    az = asin(x[0] / cos(el))
    return array([az, el])
```
````

```{dropdown} I'm uncertain how to calculate the Jacobian, H.
Luckily you don't always need to. Once you are confident in your nonlinear measurement function `h()`
then you can approximate the Jacobian numerically.
```

````{dropdown} I have a model but my results are poor.
The best thing to do is to test your model components in isolation. First, make sure that your `h()`
function is generating values very similar to what you have in `z`. The data is simulated, and for the
majority of measurements you should get a very close match.

Once that is done, the next step is to verify the Jacobian. The measurement function is pretty non-linear,
and $h(x) \neq Hx$. The easiest way to check it is using a numerical approximation as described in
the earlier hint. Here is a sample implementation you can use.
```python
delta = 1e-6
for k in range(x_and_p.estimate.shape[0]):
    dx_high = copy(x_and_p.estimate)
    dx_low = copy(x_and_p.estimate)
    dx_high[k] += delta
    dx_low[k] -= delta
    jac_col = (h(dx_high) - h(dx_low)) / (2 * delta)
    H[:, k] = jac_col.flatten()
```
Note `H` is likely sparse; if using a pinson state block you'll probably only need to verify the 6
columns corresponding to position and attitude errors.
````

```{dropdown} Click to reveal description of solution.
But if you are still struggling, one solution is stored in `.details/direction_exc_ans/`.
```
