#!/usr/bin/python3
import pickle
import time
import math
import sys

import numpy as np
import gzip

from isan.common.parameters import Para_Dict
from isan.common.task import Lattice, Base_Task, Early_Stop_Pointwise
from isan.tagging.eval import TaggingEval as Eval
from isan.tagging.ss import Word as Word
from isan.tagging.wb_tag_symbolic import Base_Features


"""
word-based tagging
"""

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
        for i,it in enumerate(line):
            if len(it)!=6 :
                l=it[:3]
                r=it[-2:]
                m=it[3:-2]
                line[i]=l+[','.join(m)]+r

        line=[[int(label),int(b),int(e),w,t,float(conf)] for label,b,e,w,t,conf in line]
        items2=[]
        gold=[]
        for l,b,e,w,t,conf in line :
            if conf <= -1  :
                conf = None
            else :
                pass
                #conf = conf/1000
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

    decode=pickle.loads
    encode=pickle.dumps

    def __init__(self,lattice,bt=init_state):
        self.extend(pickle.loads(bt))
        self.lattice=lattice

    def shift(self,showall=False):
        begin=0 if self[1]==-1 else self.lattice[self[1]][1]

        if begin not in self.lattice.begins : return []
        
        b=self.lattice.begins[begin]

        return [[n,pickle.dumps((self[1],n))] 
                for n in self.lattice.begins[begin]
                if (self.lattice[n][2][-1] is not None or showall)
                ]

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

    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    # init and weights

    def __init__(self,cmd_args,model=None,paras=None,logger=None):
        self.models={}
        self.build_ins={'word':Word,'base': Base_Features }

        if model==None :
            self.paras=paras
            self.w=paras.add({})

            self.models['base']=self.build_ins['base'](args=None,paras=self.paras)

            if hasattr(cmd_args,'task_features'):
                for k,v in cmd_args.task_features.items():
                    self.models[k]=self.build_ins[k](args=v,paras=self.paras)
        else :
            data,kv=model
            self.w=data
            for k,v in kv.items():
                self.models[k]=self.build_ins[k](model=v)
            
    def dump_weights(self) :
        d={k:v.dump_weights() for k,v in self.models.items()}
        return d

    def add_model(self,model):
        data,kv=model
        self.w.add_model(data)
        for k,v in kv.items():
            self.models[k].add_model(v)
        pass


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # actions

    class Action :
        @staticmethod
        def encode(action):
            return action[0]
        @staticmethod
        def decode(action):
            return (action,None)

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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # states

    def _next_ind(self,last_ind,action):
        next_ind=last_ind+len(self.lattice[action][2][0])
        return next_ind if next_ind != self.lattice.length else -1

    def shift(self,last_ind,stat,showall=False):
        rtn= [(a,self._next_ind(last_ind,a),s) 
                for a,s in self.State(self.lattice,stat).shift(showall)]
        return rtn

    reduce=None


    def actions_to_moves(self,actions,lattice):
        state=self.State(lattice)
        stack=[state]
        moves=[[None,None,action] for action in actions]
        moves[0][0]=0
        moves[0][1]=self.State.init_state
        for i in range(len(moves)-1) :
            move=moves[i]
            step,state,action=move
            ind,label=action
            if ind >=0 : # shift
                rst=[[nstep,ns] for a,nstep,ns in self.shift(step,state,True) if a==self.Action.encode(action)]
                moves[i+1][0],moves[i+1][1]=rst[0]
                stack.append(rst[0][1])
            else : # reduce 
                s0=stack.pop()
                s1=stack.pop()
                rst=[[nstep,ns] for a,nstep,ns,_ in self.reduce(step,s0,[0],[s1]) if a==self.Action.encode(action)]
                moves[i+1][0],moves[i+1][1]=rst[0]
                stack.append(rst[0][1])
                pass
        for move in moves:
            move[2]=self.Action.encode(move[2])

        moves=list(map(tuple,moves))
        return moves

    # feature related

    def set_raw(self,raw,Y):
        self.lattice=raw
        self.atoms=[]
        for ind in range(len(self.lattice)):
            data=self.lattice[ind]
            b=data[0]
            e=data[1]
            w,t,m=data[2]
            self.atoms.append((w,t,m,str(len(w))))
        self.atoms.append(('~','~','','0'))

        for model in self.models.values() :
            model.set_raw(self.atoms)

    def gen_features(self,state,actions,delta=0):
        ind1,ind2=self.State(self.lattice,state)
        scores=[[sum(model(ind1,ind2,ind3,delta) for model in self.models.values())]
                for ind3 in actions]
        return scores

    def cal_delta(self,std_moves,rst_moves) :
        delta=0.01 #### TODO: delta
        dirty=set()
        for b,e,data in self.lattice :
            if data[-1]==None :
                for x in range(b,e) :
                    dirty.add(x)

        max_step=max(x[0] for x in rst_moves)
        std_moves=set(x for x in std_moves if x[0]<=max_step)
        rst_moves=set(rst_moves)
        for m in std_moves-rst_moves :
            a,b=pickle.loads(m[1])
            c=m[-1]
            flag=True
            for x in [a,b,c] :
                if x==-1 : continue
                l,r,_=self.lattice[x]
                for ind in range(l,r):
                    if ind in dirty : flag=False
            if flag : 
                pass
                self._update(m,delta)
        for m in rst_moves-std_moves :
            a,b=pickle.loads(m[1])
            c=m[-1]
            flag=True
            for x in [a,b,c] :
                if x==-1 : continue
                l,r,_=self.lattice[x]
                for ind in range(l,r):
                    if ind in dirty : flag=False
            if flag : 
                pass
                self._update(m,-delta)

    def __del__(self):
        for model in self.models.values() :
            if hasattr(model,'close') :
                model.close()
