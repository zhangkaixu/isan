#!/usr/bin/python3
import re


def encode(raw,result):
    return ' '.join(['_'.join([item[0],item[1],str(head)]) for item,head in zip(raw,result)])

def decode(line):
    #print(line)
    sen=[]
    for arc in line.split():
        word,tag,head_ind,arc_type=arc.split('_')
        head_ind=int(head_ind)
        sen.append((word,tag,head_ind,arc_type))
    return {'raw':to_raw(sen),'y':sen,'Y_b':sen}
        

def to_raw(line):
    return [(w,t)for w,t,*_ in line]

def arcs_to_result(arcs,lattice):
    return arcs

def result_to_arcs(result):
    return [ind for _,_,ind,_ in result]
    pass

if __name__=="__main__":
    for line in open('/media/exp/isan/test/hit_dep.txt'):
        sen=decode(line)
        print(sen)
