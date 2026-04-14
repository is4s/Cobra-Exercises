# Exercise: Add a Direction to Known Feature Processor

In this exercise, you are tasked with adding a new processor with a more complicated measurement model.
Throughout this exercise, you will learn how to write and utilize a preprocessor in `pntos-python`.
All of the files in `exercises/direction_exercise` will need to be modified in order to fully
implement the processor.

## Motivation

Many of the measurement processors in `cobra` and features added in prior exercises are pretty basic
from a sensor modeling standpoint. Most incorporate a direct measurement of some platform parameter,
such as position or velocity. This exercise guides you through adding a new processor that
ingests an *indirect* measurement- the polar angles to features, such as might be extracted from
camera images. The measurement model is quite non-linear, and the number of observations per update
can vary. 

## Dataset

The [datafile](https://pntos.pages.aspn.us/pntos-python/example_data.html) used for this example is
the same as in the prior exercises. We'll be using the **/sensor/simulated/directiontoknownfeature**
channel.

One critical piece of information is that the sensor measurements are in a downward-looking sensor frame.
Use (0.707106781, 0.0, 0.707106781, 0.0) for the sensor to platform quaternion and (0.80, 0.0, 0.05)
for the lever arm in the sensor config.
    
## Verifying Solution

Since there is no one "right" way to write it, there is also no one "right" way to judge it either.
Instead, we have provided the results from a nominal solution that own engineers wrote below. Feel
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
We recommend starting with the easy parts- the app and the sensor plugin. If you completed the ZUPT
exercise, the process for these two pieces will be quite similar. Try and set up the app to generate
a processor that does nothing first, and then fill in the math in the processor later.
```

```{dropdown} I have the new processor, but I'm not sure how to implement the model.
The heart of a StandardMeasurementModel is the nonlinear measurement function h(). This function
takes a state vector and produces *predicted* measurements. In order to do this, you need to
understand the states you are bringing in, and the contents of the measurements.  
Have a look at the documentation for the [the python measurement class](https://git.aspn.us/pntos/firehose-outputs/-/blob/main/aspn-py/src/aspn23/measurement_direction_3d_to_points.py?ref_type=heads). Notice that the actual observations are a
list of a [nested type](https://git.aspn.us/pntos/firehose-outputs/-/blob/main/aspn-py/src/aspn23/type_direction_3d_to_point.py?ref_type=heads).
You'll need to pay attention what `reference_frame` you are dealing with.

If you are using the 'pinson' state block as in the other exercises, your processor *will* need
to ingest nominal inertial PVA data.

It is also worth mentioning that you have some leeway in what the measurement vector z contains-
you do not necessarily need to use the raw measurement observations in their original format.
```


````{dropdown} Click to reveal description of solution.

But if you are still struggling, one solution is stored in `.details/direction_exc_ans/`.
```
