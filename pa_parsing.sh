#!/bin/sh
./isan.py \
    --model isan.common.perceptrons.Model_PA \
    --decoder isan.common.decoder.Push_Down \
    --task isan.parsing.default_dep.PA_Dep \
    $*
