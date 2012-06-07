#!/usr/bin/python3
import isan.tagging.inc_segger as inc_segger
import argparse
import sys

def make_green(s):
    return '\033[32;01m%s\033[1;m'%s

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="分词模型")
    parser.add_argument('model_file',help='模型文件')
    args=parser.parse_args()
    #print(args)
    print("使用模型文件%s分词"%(make_green(args.model_file)),file=sys.stderr)
    model=inc_segger.Model(args.model_file,
                inc_segger.Defalt_Actions(
                )
        )
    model=inc_segger.Model(args.model_file)
    
    for line in sys.stdin:
        line=line.strip()
        print(*model(line))
