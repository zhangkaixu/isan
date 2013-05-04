#!/usr/bin/python3
import pickle
import time
import math
import sys
from isan.common.task import Lattice, Base_Task, Early_Stop_Pointwise
from isan.tagging.eval import TaggingEval as Eval


class codec :
    @staticmethod
    def decode(line):
        """
        编码、解码
        从一行文本中，得到输入（raw）和输出（y）
        """
        if not line: return []
        log2=math.log(2)
        line=list(map(lambda x:x.split(','), line.split()))
        line=[[int(label),int(b),int(e),w,t,int(conf)] for label,b,e,w,t,conf in line]
        items2=[]
        gold=[]
        for l,b,e,w,t,conf in line :
            if conf != -2:
                if conf == -1 :
                    conf = None
                else :
                    conf = str(math.floor(math.log(conf/500+1)))
                items2.append((b,e,(w,t,conf)))
            if l ==1 :
                gold.append((w,t))
        raw=Lattice(items2)
        return {'raw':raw,
                'y':gold, }
    @staticmethod
    def encode(y):
        return ' '.join(y)

class State (list):
    init_state=pickle.dumps((-1,-1))

    def __init__(self,lattice,bt=init_state):
        self.extend(pickle.loads(bt))
        self.lattice=lattice

    def shift(self):
        begin=0 if self[1]==-1 else self.lattice[self[1]][1]
        rtn=[[n,pickle.dumps((self[1],n))] for n in self.lattice.begins[begin]]
        return rtn

    def dumps(self):
        return pickle.dumps(tuple(self))

    @staticmethod
    def load(bt):
        return pickle.loads(bt)

class Path_Finding (Early_Stop_Pointwise, Base_Task):
    """
    finding path in a DAG
    """
    name='joint chinese seg&tag from a word-tag lattice'
    codec=codec
    State=State
    Eval=Eval

    class Action :
        @staticmethod
        def encode(action):
            return action[0]
        @staticmethod
        def decode(action):
            return (action,None)


    # actions

    def result_to_actions(self,result):
        offset=0
        actions=[]
        for g in result :
            nex=[[ind,self.lattice[ind]] for ind in self.lattice.begins[offset]]
            nex=[ind for ind, it in nex if (it[2][0],it[2][1])==g]
            actions.append((nex[0],None))
            offset+=len(g[0])
        return actions

    def actions_to_result(self,actions):
        seq=[self.lattice[action[0]] for action in actions]
        seq=[(it[0],it[1])for _,_,it in seq]
        return seq

    # states

    def next_ind(self,last_ind,action):
        next_ind=last_ind+len(self.lattice[action][2][0])
        next_ind= next_ind if next_ind != self.lattice.length else -1
        return next_ind

    def shift(self,last_ind,stat):
        state=self.State(self.lattice,stat)
        for a,s in state.shift():
            self.next_ind(last_ind,a)
        rtn=[(a,self.next_ind(last_ind,a),s) for a,s in state.shift()]
        return rtn

    reduce=None


    # feature related

    def set_raw(self,raw,Y):
        self.lattice=raw

    def gen_features(self,state,actions):
        fvs=[]
        state=self.State(self.lattice,state,)
        ind1,ind2=state
        if ind1==-1 :
            w1,t1,m1='~','~',''
            len1='0'
        else :
            w1,t1,m1=self.lattice[ind1][2]
            len1=str(w1)
        
        if ind2==-1 :
            w2,t2,m2='~','~',''
            len2='0'
        else :
            w2,t2,m2=self.lattice[ind2][2]
            len2=str(w2)

        for action in actions :
            ind3=action
            if ind3==-1 :
                w3,t3,m3='~','~',''
                len3='0'
            else :
                w3,t3,m3=self.lattice[ind3][2]
                len3=str(w3)

            fv=((['m3~'+m3,] if m3 is not None else [])+
                    (['m3m2~'+m3+'~'+m2,] if m3 is not None  and m2 is not None else [])+
            [
                    'w3~'+w3, 't3~'+t3, 'l3~'+len3,
                    'w3t3~'+w3+t3, 'l3t3~'+len3+t3,

                    'w3w2~'+w3+"-"+w2, 'w3t2~'+w3+t2,
                    't3w2~'+t3+w2, 't3t2~'+t3+t2,

                    'l3w2~'+len3+w2, 'w3l2~'+w3+'~'+len2,
                    'l3t2~'+len3+t2, 'l3l2~'+len3+'~'+len2,

                    'w3t3l2~'+w3+t3+'~'+len2,
                    'w3t3w2~'+w3+t3+w2, 'w3w2t2~'+w3+t2+w2,
                    
                    't3t1~'+t3+t1, 't3t2t1~'+t3+t2+t1,
                    'l3l2l1~'+len3+'~'+len2+'~'+len1,
                    ])
            fvs.append(fv)
        return fvs

