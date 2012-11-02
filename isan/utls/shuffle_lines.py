#!/usr/bin/python3
import argparse
import random
import sys

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description="随机化文件的行")
    parser.add_argument('filename',help='要操作的文件名',nargs='+')
    parser.add_argument('-i',help='不设定会输出到标准输出流，设定后写回原文件',action='store_true',dest='i')
    args=parser.parse_args()

    data=[]
    for lines in zip(*[open(fn) for fn in args.filename]):
        data.append([line.strip() for line in lines])
    random.shuffle(data)
    out_file=[sys.stdout if not args.i else open(fn,'w') for fn in args.filename]
    for ls in data:
        for l,f in zip(ls,out_file) :
            print(l,file=f)
    exit()

