#!/usr/bin/python3
import re
import sys
import argparse
import json

def wiki_reader(line):
    line=re.sub(r'^([^\[]*)\]\]',r'\1',line)
    line=re.sub(r'\[\[([^\]]*)$',r'\1',line)
    if '[[' not in line : return None
    line=re.split('(\[\[[^\]]+\]\])',line)
    line=[x for x in line if x]
    word_start_at=-1
    intervals=[[-1,-1]]
    offset=0
    raw=[]
    for w in line:
        in_word=0
        if w[:2]=='[[':
            w=w[2:-2]
            in_word=1
        else :
            pass
        raw.append(w)
        for c in w[:-1]:
            if in_word:
                intervals.append([offset,offset+len(w)])
            else :
                intervals.append([-1,-1])
        intervals.append([-1,-1])
        offset+=len(w)
    raw=''.join(raw)
    if not(len(raw)+1==len(intervals)):
        input('assert')
        return None
    return {'raw':raw,'Y':[None,intervals]}

def seg_reader(line) :
    y=line.split()
    return {'seg' : y, 'Y' : None}

def raw_reader(data) :
    data=data.strip()
    return {'raw' : data,'Y': None}
def raw_writer(data) :
    if 'raw' in data : return data['raw']
    if 'seg' in data : return ''.join(data['seg'])

def seg_writer(data) :
    if 'seg' in data : return data['seg']
    return None

def raw_with_Ya_writer(data) :
    raw=raw_writer(data)
    Y=None
    if 'Y' in data :
        Y=data['Y']
    return json.dumps({'raw' : raw,'y': seg_writer(data),
        'Y_a' : Y},ensure_ascii=False)
def raw_with_Ya_reader(data) :
    data=json.loads(data)
    raw=data.get('raw')
    Ya=data.get('Y_a',None)
    return {'raw':raw,'Y':Ya}

def raw_with_Yb_writer(data) :
    raw=raw_writer(data)
    Y=None
    if 'Y' in data :
        Y=data['Y']
    return json.dumps({'raw' : raw,'y': seg_writer(data),
        'Y_b' : Y},ensure_ascii=False)
def raw_with_Yb_reader(data) :
    data=json.loads(data)
    raw=data.get('raw')
    Ya=data.get('Y_b',None)
    return {'raw':raw,'Y':Ya}

if __name__ == '__main__':
    readers={'raw':raw_reader,
            'seg':seg_reader,
            'wiki':wiki_reader,
            'Ya': raw_with_Ya_reader,
            'Yb': raw_with_Yb_reader,
            }
    writers={'raw': raw_writer,
            'Ya': raw_with_Ya_writer,
            'Yb':raw_with_Yb_writer,
            }

    parser=argparse.ArgumentParser(description="分词相关的格式转换")
    parser.add_argument('-f','--from',dest='reader',
            choices=readers,
            metavar='源格式')
    parser.add_argument('-t','--to',
            dest='writer',default='raw',
            choices=writers,
            metavar='目标格式')
    args=parser.parse_args()
    reader=readers[args.reader]
    writer=writers[args.writer]


    for line in sys.stdin :
        line=line.strip()
        data=reader(line)
        if data :
            print(writer(data))
        

