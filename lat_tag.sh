#!/bin/sh
./isan.py \
    --model isan.common.perceptrons.Model \
    --decoder isan.common.decoder.Push_Down \
    --task isan.tagging.lat_tagger.Dep \
    $*
