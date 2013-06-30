#!/usr/bin/python3
import argparse
import gzip
import pickle
import math
import sys


if __name__ == '__main__':
    argv=sys.argv[1:]
    dst=argv[-1]
    models=argv[:-1]

    weights={}
    numbers={}

    #models=['model_train_'+str(x)+'.txt' for x in [0,1,2,3,4]]
    #models=['model_'+str(x)+'.gz' for x in [1,2,3,4,5]]
    for model in models:
        print(model)
        for k,v in pickle.load(gzip.open(model)).items():
            if k not in weights :
                weights[k]=0
                numbers[k]=0
            weights[k]+=v
            if v!=0 : numbers[k]+=1


    for k,n in numbers.items():
        if n!=0 :
            #weights[k]=round(weights[k]/max(n-0.5,1))
            weights[k]=round(weights[k]/n)
            #weights[k]=round(weights[k]/len(models))

    pickle.dump(weights,gzip.open(dst,'wb'))

