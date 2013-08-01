#!/usr/bin/python3
import sys
"""!
@mainpage

Isan
====
一个中文处理的实验环境


ls test/*.train | sed 's/^\([^\.]*\)\.train/shuffle -m 20 -d .\/\1 -p 5 seg --train \1.train --dev \1.test --iteration 15 --yaml args.yaml /g' | xargs -n 16 -P 1 ./isan.sh


seq 0 9 | awk '{print "test/" $1 "/model.gz --input test/" $1 ".test"}' | xargs -d "\n" -n 1 ./isan.sh seg --threshold 20 --yaml args.yaml --output t.lat --append
"""


from isan import *

if __name__ == '__main__':
    this,*argv=sys.argv
    """
    if len(argv)==0 :
        exit()
    if argv[0]=='seg':
        argv[0:1]= (['--model', 'isan.common.perceptrons.Model']+
            ['--decoder', 'isan.common.decoder.First_Order_Linear']+
            ['--task', 'isan.tagging.cb_cws.Task'])
    
    """
    
    isan(**get_args(argv))

