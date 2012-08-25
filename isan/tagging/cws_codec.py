#!/usr/bin/python3
"""
每一行是一个单位，各个单位独立
单位支持多种格式
最简单的格式是用空格隔开的文字，即表示了分词结果，又蕴涵了原始句子
扩展的格式是用json编码。
    一种扩展的格式是这样的：["原始句子",[已知的成分的开始和结尾],[各个间隔断开和连接可选值]]
"""
import sys
import json
"""

"""



def decode(line):
    if not line: return []
    if line[0]!='[':
        seq=[word for word in line.split()]
        raw=''.join(seq)
        return raw,seq,None
    data=json.loads(line)
    if not data[0] and data[1]:
        data[0]=''.join(data[1])
    return data
        

def encode(seq):
    return ' '.join(seq)

def to_raw(seq):
    if not seq: return ''
    if type(seq[0])!=str:
        return ''.join(a for a,_ in seq)
    else:
        return ''.join(seq)

