#!/usr/bin/python3
import sys
import argparse

def to_full(text,ignore=set()):
    """
    半角转全角的程序
        空格变成全角
        大于空格的直接加上偏移量
        否则不变
    """
    
    return ''.join(
                    chr(x) if (x<32 or x>128 or x in ignore) else 
                    chr(12288) if x==32 else chr(x+65248) 
            for x in map(ord,text))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description="")
    parser.add_argument('--ignore',help='忽略的',dest='ignore',type=str)
    parser.add_argument('--check',help='只显示改变了的',action='store_true')
    args=parser.parse_args()
    ignore=set()
    if args.ignore :
        for c in sys.argv[1] :
            ignore.add(ord(c))
        
    for line in sys.stdin :
        line=line.strip()
        if args.check :
            rtn=to_full(line,ignore)
            if line!=rtn :
                print(rtn)
        else :
            print(to_full(line,ignore))
    pass

