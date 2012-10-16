#!/bin/sh

./isan.py \
    --model isan.common.perceptrons.Model_PA \
    --decoder isan.common.decoder.DFA \
    --task isan.tagging.PA_segger.Segger \
    $*
