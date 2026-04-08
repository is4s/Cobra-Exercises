#!/usr/bin/env bash

# Warning: This file expects to be run from the root level directory
# Generates .patch files for exercises in the apps

git diff --no-index exercises/zupt_exercise/zupt_app.py .details/zupt_exc_ans/zupt_app.py > util/zupt_app.patch
