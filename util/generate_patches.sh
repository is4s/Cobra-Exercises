#!/usr/bin/env bash

# Warning: This file expects to be run from the root level directory
# Generates .patch files for exercises in the apps

git diff --no-index exercises/zupt_exercise/zupt_app.py .details/zupt_exc_ans/zupt_app.py > util/zupt_app.patch
git diff --no-index exercises/new_app_exercise/pos_baro_app.py .details/new_app_exc_ans/pos_baro_app.py > util/pos_baro_app.patch
git diff --no-index exercises/direction_processor_exercise/direction_app.py .details/direction_exc_ans/direction_app.py > util/direction_app.patch
