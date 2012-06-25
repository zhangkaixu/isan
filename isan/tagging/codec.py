#!/usr/bin/python3
"""
每一行是一个单位，各个单位独立
单位支持多种格式
最简单的格式是用空格隔开的文字，即表示了分词结果，又蕴涵了原始句子
扩展的格式是用json编码。
    一种扩展的格式是这样的：["原始句子",[已知的成分的开始和结尾],[各个间隔断开和连接可选值]]
"""
import sys
"""

"""
def decode(line,sep='_'):
    if not line: return []
    if line[0]!='[':
        seq=[item.partition(sep) for item in line.split(' ')]
        if not seq:return []
        if(seq[0][1]==''):
            return [word for word,_,tag in seq]
        
        return [[word, tag] for word,_,tag in seq]


def encode(seq,sep='_'):
    if type(seq[0])!=str:
        return ' '.join(a+sep+b for a,b in seq)
    else:
        return ' '.join(seq)

def to_raw(seq):
    if not seq: return ''
    if type(seq[0])!=str:
        return ''.join(a for a,_ in seq)
    else:
        return ''.join(seq)

if __name__=="__main__":
    
    print(encode([['a','b']]))
