#!/bin/sh

if [ $# = 0 ]; then
    echo “举一隅不以三隅反，则不复也” ——《论语·述而》
    exit
fi

if [ $1 = 'link' ] ; then
    echo 'link'
    src=$(dirname $0)
    ln -s ${src}/isan .
    ln -s ${src}/isan.py .
    ln -s ${src}/isan.sh .
fi

#
# 中文分词模型
#
if [ $1 = 'seg' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.First_Order_Linear \
        --task isan.tagging.cb_cws.Task \
        $@
fi

if [ $1 = 'dep' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.Push_Down \
        --task isan.parsing.default_dep.Dep \
        $@
fi

if [ $1 = 'cws' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.DFA \
        --task isan.tagging.cws.Task \
        $@
fi

if [ $1 = 'tag' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.DFA \
        --task isan.tagging.wb_tag.Path_Finding \
        $*
fi


if [ $1 = 'lat_dep' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.Push_Down \
        --task isan.parsing.lat_dep.Dep \
        $@
fi

if [ $1 = 'pa_cws' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model_PA \
        --decoder isan.common.decoder.DFA \
        --task isan.tagging.PA_segger.Segger \
        $*
fi

if [ $1 = 'pa_parsing' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model_PA \
        --decoder isan.common.decoder.Push_Down \
        --task isan.parsing.default_dep.PA_Dep \
        $*
fi

if [ $1 = 'seg_dep' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.Push_Down \
        --task isan.parsing.seq_dep.Dep \
        $*
fi

if [ $1 = 'tagpath' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.DFA \
        --task isan.tagging.tagging_dag.Path_Finding \
        $*
fi

if [ $1 = 'dep' ] ; then
    shift
    ./isan.py \
        --model isan.common.perceptrons.Model \
        --decoder isan.common.decoder.Push_Down \
        --task isan.parsing.default_dep2.Dep \
        $*
fi
