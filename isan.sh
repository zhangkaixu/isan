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


if [ $1 = 'stack' ] ; then
    src=$2
    batch=$3 # batchsize
    fold=$4
    dst=$5
    for tgt in `seq 0 $(expr $fold - 1 ) `; do
        cat $src | awk "(NR-NR%${batch})/${batch}%${fold}==${tgt} {print}" > ${dst}/${tgt}.test
        cat $src | awk "(NR-NR%${batch})/${batch}%${fold}!=${tgt} {print}" > ${dst}/${tgt}.train
    done;
    
    exit
fi

if [ $1 = 'shuffle' ] ; then
    cmd=$0
    shift
    if [ $# = 0 ]; then
        echo "usage:"
        echo "    " ${cmd} shuffle -p processor-number=1 -m model-number=1 -d dir=. blabla
        exit
    fi
    dst='.' # dir
    nm='1' # number of models
    np='1'
    while [ `echo $1 | grep '\-'` ] ; do
        if [ `echo $1 | grep '\-p'` ] ; then
            np=$2
            shift;shift
        fi
        if [ `echo $1 | grep '\-d'` ] ; then
            dst=$2
            shift;shift
        fi
        if [ `echo $1 | grep '\-m'` ] ; then
            nm=$2
            shift;shift
        fi
    done
    echo "train [\033[34m$nm\033[0m] model(s)" "into [\033[34m$dst\033[0m]"
    echo "using [\033[34m$np\033[0m] processor(s)"
    echo "the command line is:\033[34m${cmd} $*\033[0m"

    #exit

    mkdir $dst -p
    echo `for i in $(seq $nm); do echo "${dst}/model.$i.gz --seed $i"; done` | xargs  -n 3 -P $np ${cmd} $*
    ${cmd} $1 ${dst}/model.gz --append_model `for i in $(seq $nm); do echo "${dst}/model.$i.gz"; done`
    exit
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
