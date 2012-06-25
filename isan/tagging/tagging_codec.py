#!/usr/bin/python3
"""
"""
import sys
"""
"""
def decode(line):
    if not line: return []
    seq=[item.split('_') for item in line.split(' ')]
    return seq
        

def encode(seq):
    return ' '.join(word+"_"+tag for word,tag in seq)

def to_raw(seq):
    if not seq: return ''
    return ''.join(a for a,_ in seq)

