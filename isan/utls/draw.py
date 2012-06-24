#!/usr/bin/python3
import os
import sys
import subprocess

def exp_tree(line,node,head,src):
    if len(node[head])==1:return
    node[head].sort()
    for ind in node[head]:
        if ind!=head:
            src.append('"%d"[label="%s"];'%(ind,line[ind][1][0]))
            src.append("%d->%d;"%(head,ind))
        else:
            src.append('"~%d"[label="~",shape="point"];'%(head))
            src.append('%d->"~%d";'%(head,head))
    for ind in node[head]:
        if ind !=head:
            exp_tree(line,node,ind,src)
def encode(line,T='png'):
    line=[[ind,item.split('_')] for ind,item in enumerate(line.split())]
    node=[[ind] for ind in range(len(line))]
    head=-1
    for ind,item in line:
        item[2]=int(item[2])
        if item[2]==-1:
            head=ind
        else:
            node[item[2]].append(ind)
    src=["digraph unix {",
            "node[shape=box];",
            "rankdir=TD;"]
    src.append('"%d"[label="%s"];'%(head,line[head][1][0]))
    exp_tree(line,node,head,src)
    src.append("}")
    src='\n'.join(src)
    dot=subprocess.Popen(["dot","-T"+T],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    stdout,stderr=dot.communicate(src.encode())
    return stdout

if __name__=="__main__":
    line='''导弹_NN_2 不_AD_2 必_VV_22 带_VV_2 弹头_NN_3 ，_PU_22 目标_NN_8 不_AD_8 必_VV_13 在_VV_8 有_VE_11 居民_NN_9 之_DEC_8 地_NN_22 ，_PU_22 例如_AD_22 次要_JJ_17 外岛_NN_20 或_CC_20 领海_NN_20 边缘_NN_22 皆_AD_22 可_VV_-1 。_PU_22'''
    if len(sys.argv)<2:
        print('请输入要保存的文件名')
        exit()
    filename=sys.argv[1]

    for line in sys.stdin:
        open(filename,'wb').write(encode(line))
        exit()
