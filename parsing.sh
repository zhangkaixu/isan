#!/bin/sh
./isan.py --model isan.common.perceptrons.Base_Model --decoder isan.common.searcher.Push_Down --task isan.parsing.default_dep.Dep $*
