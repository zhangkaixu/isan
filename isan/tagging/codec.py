#!/usr/bin/python3
def decode(line,sep='_'):
    seq=[item.partition(sep) for item in line.split(' ')]
    if not all(sep==item[1] for item in seq):
        print("error")
        return []
    return [[word, tag] for word,_,tag in seq]


def encode(seq,sep='_'):
    if type(seq[0])!=str:
        return ' '.join(a+sep+b for a,b in seq)
    else:
        return ' '.join(seq)
if __name__=="__main__":
    
    print(encode([['a','b']]))
