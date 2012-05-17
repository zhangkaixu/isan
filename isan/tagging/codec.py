#!/usr/bin/python3
import sys
def decode(line,sep='_'):
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
if __name__=="__main__":
    
    print(encode([['a','b']]))
