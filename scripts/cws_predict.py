#!/usr/bin/python3
import isan.tagging.inc_segger as inc_segger
import argparse
import sys

def make_color(s):
    #return '\033[32;01m%s\033[1;m'%s  #green
    #return '\033[35;01m%s\033[1;m'%s #purple
    return '\033[36;01m%s\033[1;m'%s #blue

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="分词模型")
    parser.add_argument('model_file',help='模型文件')
    parser.add_argument('-t','--test',help='测试用文件',dest='test_file')
    args=parser.parse_args()
    #print(args)
    print("使用模型文件%s分词"%(make_color(args.model_file)),file=sys.stderr)
    model=inc_segger.Model(args.model_file,
                inc_segger.Defalt_Actions(
                )
        )
    model=inc_segger.Model(args.model_file)
    
    if args.test_file:

        print("使用已分词的文件%s作为测试集"%(make_color(args.test_file)),file=sys.stderr)
        model.test(args.test_file)
        exit()
    print("以%s作为输入，以%s作为输出"%(make_color('标准输入流'),make_color('标准输出流')),file=sys.stderr)
    for line in sys.stdin:
        line=line.strip()
        print(*model(line))
