#!/usr/bin/python3
from collections import Counter
import argparse
import sys

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description="")
    parser.add_argument('-m','--min',type=int,help='',dest='min',default=1)
    parser.add_argument('--kv',type=bool,help='',default=False)
    args=parser.parse_args()
    
    #print(args.min)
    c=Counter()
    for line in sys.stdin:
        line=line.strip()
        if args.kv :
            k,_,v=line.rpartition(' ')
            c.update({k : float(v)})
            
            pass
        if line:
            c.update({line:1})

    for k,v in c.most_common():
        if v<args.min: break
        print(k,v)


