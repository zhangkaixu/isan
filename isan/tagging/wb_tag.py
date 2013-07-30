#!/usr/bin/python3
import pickle
import time
import math
import sys
from isan.common.task import Lattice, Base_Task, Early_Stop_Pointwise
from isan.tagging.eval import TaggingEval as Eval
import numpy as np
import gzip

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
            if conf <= -1 :
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

    def __init__(self,cmd_args,logger=None):

        self.models=[]
        #self.models=[SubSym()]
        #self.models.append(Word())
        #self.models.append(Bigram())
        #self.models.append(Trigram())

        if(hasattr(cmd_args,'debug')): self.debug=True
        if hasattr(self,'debug'):
            self.char_weights={}
            for line in open('weights.txt'):
                line=line.split()
                if len(line)!=3 : 
                    line[-2]=int(line[-2])
                self.char_weights[tuple(line[:-1])]=float(line[-1])

        """
        self.ae={}
        for line in open('ae_output.txt'):
            word,*inds=line.split()
            self.ae[word]=inds
            """

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

        

        b=0
        l=max(x[1] for x in self.lattice)
        seq=['' for i in range(l)]
        for b,e,data in self.lattice :
            for i in range(len(data[0])):
                seq[b+i]=data[0][i]
        seq=''.join(seq)
        uni_chars=list(x for x in '##'+seq+'###')
        bi_chars=[uni_chars[i]+uni_chars[i+1]
                for i in range(len(uni_chars)-1)]
        self.uni_chars=uni_chars
        self.uni_fv=[]
        for ind in range(len(seq)+1):
            c_ind=ind+2
            self.uni_fv.append([])
            for ws_current in 'BMES':
                self.uni_fv[-1].append([
                        [uni_chars[c_ind-1],2,ws_current],
                        [uni_chars[c_ind],1,ws_current],
                        [uni_chars[c_ind+1],0,ws_current],
                        [bi_chars[c_ind-2],3,ws_current],
                        [bi_chars[c_ind-1],2,ws_current],
                        [bi_chars[c_ind],1,ws_current],
                        [bi_chars[c_ind+1],0,ws_current],
                        ])

        self.atoms=[]
        for ind in range(len(self.lattice)):
            data=self.lattice[ind]
            b=data[0]
            e=data[1]
            w,t,m=data[2]
            cb=[]
            if b+1==e :
                cb+=self.uni_fv[b][3]
            else :
                cb+=self.uni_fv[b][0]
                for i in range(b+1,e-1):
                    cb+=self.uni_fv[i][1]
                cb+=self.uni_fv[e-1][2]
            cb=[(p+'-'+t,k,ind) for k,ind,p in cb]
            if b+1<e :
                if b+2==e :
                    cb+=[('B-'+t,'E-'+t)]
                else :
                    cb+=[('B-'+t,'M-'+t)]
                    cb+=[('M-'+t,'M-'+t) for i in range(e-b-3)]
                    cb+=[('M-'+t,'E-'+t)]
            if hasattr(self,'debug'):
                if cb :
                    cb=sum(self.char_weights[x] for x in cb if x in self.char_weights)
                else :
                    cb=0
                pass
            self.atoms.append((w,t,m,str(len(w)),cb))
        self.atoms.append(('~','~','','0',0))

        for model in self.models :
            model.set_raw(self.atoms)

    def gen_features(self,state,actions,delta=0,step=0):
        strm=lambda x:'x' if x=='' else str(math.floor(math.log((x if x>0 else 0)*2+1)))
        fvs=[]
        state=self.State(self.lattice,state,)
        ind1,ind2=state

        w1,t1,m1,len1,cb1=self.atoms[ind1]
        w2,t2,m2,len2,cb2=self.atoms[ind2]

        scores=[]
        for action in actions :
            ind3=action
            w3,t3,m3,len3,cb3=self.atoms[ind3]
            score=0#m3*self.m_d[0] if m3 is not None else 0
            for model in self.models :
                score+=model(ind1,ind2,ind3,delta*0.1,step)

            fv=[]
            #"""
            fv=(
                #(['m3~'+strm(m3), ] if m3 is not None else []) +
                    #([ 'm3m2~'+strm(m3)+'~'+strm(m2), ] if m3 is not None  and m2 is not None else [])+
            [
                    'w3~'+w3, 't3~'+t3, 'l3~'+len3, 'w3t3~'+w3+t3, 'l3t3~'+len3+t3,

                    'w3w2~'+w3+"~"+w2, 'w3t2~'+w3+t2, 't3w2~'+t3+w2, 't3t2~'+t3+t2,

                    'l3w2~'+len3+'~'+w2, 'w3l2~'+w3+'~'+len2, 'l3t2~'+len3+'~'+t2, 't3l2~'+t3+'~'+len2,
                    'l3l2~'+len3+'~'+len2,
                    
                    't3t1~'+t3+'~'+t1, 't3t2t1~'+t3+'~'+t2+'~'+t1,
                    'l3l1~'+len3+'~'+len1, 'l3l2l1~'+len3+'~'+len2+'~'+len1,
                    ])#"""
            #"""
            if hasattr(self,'debug'):
                score+=cb3
                if len2 :
                    l2=('S-' if len2=='1' else 'E-')+t2
                    l3=('S-' if len3=='1' else 'B-')+t3
                    score+=self.char_weights.get((l2,l3),0)
                #print(w2,t2,w3,t3,l2,l3)
                #"""
            #print(w3,t3,fv)
            fvs.append(fv)
            scores.append(score)


        if delta==0 :
            rtn= [[self.weights(fv)+s] for fv,s in zip(fvs,scores)]
            return rtn
        else :
            for fv in fvs :
                #print(fv,delta,step)
                self.weights.update_weights(fv,delta,step)
            return [[] for fv in fvs]
        return fvs

    def update_moves(self,std_moves,rst_moves,step) :
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
                self._update(m,1,step)
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
                self._update(m,-1,step)
    """

    def update_moves(self,std_moves,rst_moves,step) :
        #print(self.lattice)
        for s,r in zip(std_moves,rst_moves) :
            #print(pickle.loads(s[1]),s[2],pickle.loads(r[1]),r[2])
            if s!= r:
                self._update(s,1,step)
                self._update(r,-1,step)
                break
    """

    def average_weights(self,step):
        self.weights.average_weights(step)
        for model in self.models:
            model.average_weights(step)

    def un_average_weights(self):
        self.weights.un_average_weights()
        for model in self.models:
            model.un_average_weights()
