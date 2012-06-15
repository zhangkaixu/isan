#!/usr/bin/python3
import re




def decode(line):
    sen=[]
    for arc in line.split():
        word,tag,head_ind,arc_type=arc.split('_')
        head_ind=int(head_ind)
        sen.append((word,tag,head_ind,arc_type))
    return sen
        


if __name__=="__main__":
    for line in open('/media/exp/isan/test/hit_dep.txt'):
        sen=decode(line)
        print(sen)
