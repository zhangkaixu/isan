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
        line=[[int(label),int(b),int(e),w,t,int(conf)] for label,b,e,w,t,conf in line]
        items2=[]
        gold=[]
        for l,b,e,w,t,conf in line :
            if conf != -2:
                if conf == -1 :
                    conf = None
                else :
                    #conf = str(math.floor(math.log(conf/500+1)))
                    conf = conf/1000
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

    def shift(self):
        begin=0 if self[1]==-1 else self.lattice[self[1]][1]
        return [[n,pickle.dumps((self[1],n))] 
                for n in self.lattice.begins[begin]]

    def dumps(self):
        return pickle.dumps(tuple(self))

    @staticmethod
    def load(bt):
        return pickle.loads(bt)

class Word : 
    def __init__(self):
        words={}
        for line in open('word.pca') :
            word,*vs = line.split()
            vs=list(map(float,vs))
            words[word]=np.array(vs)
        tags={}
        for line in open('tag.pca'):
            tag,*vs=line.split()
            vs=list(map(float,vs))
            tags[tag]=np.array(vs)
        self.words=words
        self.tags=tags
        self.z=np.zeros(50)
        self.tz=np.zeros(10)
        gz=gzip.open('2to3.gz','rb')
        self.Ws=[]
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.V=np.array(pickle.load(gz))
        self.b=np.array(pickle.load(gz))
        self.bp=np.array(pickle.load(gz))


        self.d={}
        self.d['z']=np.zeros(20)
        self.s={k:v.copy()for k,v in self.d.items()}

    def set_raw(self,atoms):
        self.atoms=atoms
        self.fvs=[]
        for at in self.atoms :
            word=at[0]
            tag=at[1]
            key=(word,tag)
            wv=self.words.get(word,self.z)
            tv=self.tags.get(tag,self.tz)
            x=np.dot(wv,self.Ws[0])+np.dot(tv,self.Ws[1])+self.b
            fv=np.tanh(x)
            self.fvs.append(fv)


    def __call__(self,ind1,ind2,ind3,delta=0,step=0) :
        fv=self.fvs[ind3]
        if delta==0 :
            return np.dot(fv,self.d['z'])
        else :
            self.d['z']+=delta*fv
            self.s['z']+=delta*step*fv
            return 0

    def average_weights(self,step):
        self._b={}
        for k in self.d :
            self._b[k]=self.d[k].copy()
            self.d[k]-=self.s[k]/step

    def un_average_weights(self):
        self.d={}
        for k in self._b :
            self.d[k]=self._b[k].copy()


class SubSym :
    def __init__(self):
        self.words={}
        self.miss=np.zeros(50)
        for line in open('em.txt'):
        #for line in open('ss.pca'):
        #for line in open('ae.txt'):
        #for line in open('ae_vec.txt'):
            word,*vec=line.split()
            vec=list(map(float,vec))
            vec=np.array(vec)
            #self.words[word]=vec*2-1
            self.words[word]=vec
        self.d={}
        self.s={}

        self.one=np.zeros(50)
        self.one[0]=1
    def get(self,key,vec):
        if key not in self.d or vec is None : return 0
        return np.dot(self.d[key],vec)
    def _update(self,key,vec,delta,step):
        if vec is None : return
        if key not in self.d :
            self.d[key]=0
            self.s[key]=0
            self.d[key]+=vec*delta
            self.s[key]+=delta*step*vec

    def average_weights(self,step):
        self.b={}
        for k in self.d :
            self.b[k]=self.d[k].copy()
            self.d[k]-=self.s[k]/step
    def un_average_weights(self):
        self.d={}
        for k in self.b :
            self.d[k]=self.b[k].copy()

    def __call__(self,it1,it2,it3,delta=0,step=0) :
        w1,t1,m1,len1,_=it1
        w2,t2,m2,len2,_=it2
        w3,t3,m3,len3,ind3=it3
        if delta==0 :
            score=0
            em3=self.words.get(w3,None) if len3!='1' else self.one
            #em3=self.words.get(w3,None)
            for key in [
                    't3'+t3+('1' if len3!='1' else '0'),
                    #'t2'+t2,
                    ] :
                score+=self.get(key,em3)
            return score
        else :
            em3=self.words.get(w3,None) if len3!='1' else self.one
            #em3=self.words.get(w3,None)
            for key in [
                    't3'+t3+('1' if len3!='1' else '0'),
                    #'t2'+t2,
                    ] :
                self._update(key,em3,delta,step)
            return 0


class Path_Finding (Early_Stop_Pointwise, Base_Task):
    """
    finding path in a DAG
    """
    name='joint chinese seg&tag from a word-tag lattice'
    codec=codec
    State=State
    Eval=Eval

    def __init__(self,args):

        self.models=[]
        #self.models=[SubSym()]
        self.models.append(Word())
        self.ae={}
        for line in open('ae_output.txt'):
            word,*inds=line.split()
            self.ae[word]=inds

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

    def shift(self,last_ind,stat):
        return [(a,self._next_ind(last_ind,a),s) 
                for a,s in self.State(self.lattice,stat).shift()]

    reduce=None



    # feature related

    def set_raw(self,raw,Y):
        self.lattice=raw
        self.atoms=[]
        for ind in range(len(self.lattice)):
            data=self.lattice[ind]
            w,t,m=data[2]
            inds=self.ae.get(w,['^']) if len(w)>1 else ['$']
            self.atoms.append((w,t,m,str(len(w)),inds))
        self.atoms.append(('~','~','','0',[]))

        for model in self.models :
            model.set_raw(self.atoms)


        """
        b=0
        seq=[]
        while b in self.lattice.begins :
            ind=self.lattice.begins[b][0]
            _,b,d=self.lattice[ind]
            seq.append(d[0])
        seq=''.join(seq)
        #print(seq)
        uni_chars=list(x for x in '##'+seq+'###')
        bi_chars=[uni_chars[i]+uni_chars[i+1]
                for i in range(len(uni_chars)-1)]
        self.uni_chars=uni_chars
        self.uni_fv=[]
        #print(uni_chars)
        #print(bi_chars)
        for ind in range(len(seq)+1):
            c_ind=ind+2
            self.uni_fv.append([])
            for ws_current in 'BMES':
                self.uni_fv[-1].append([
                    'CH1'+uni_chars[c_ind-1]+ws_current,
                    "CH2"+uni_chars[c_ind]+ws_current,
                    "CH3"+uni_chars[c_ind+1]+ws_current,
                    "CHa"+bi_chars[c_ind-2]+ws_current,
                    "CHb"+bi_chars[c_ind-1]+ws_current,
                    "CHc"+bi_chars[c_ind]+ws_current,
                    "CHd"+bi_chars[c_ind+1]+ws_current,
                ])
        """
        #print(self.uni_fv)



    def gen_features(self,state,actions,delta=0,step=0):
        strm=lambda x:'x' if x=='' else str(math.floor(math.log(x*2+1)))
        fvs=[]
        state=self.State(self.lattice,state,)
        ind1,ind2=state

        w1,t1,m1,len1,ae1=self.atoms[ind1]
        w2,t2,m2,len2,ae2=self.atoms[ind2]

        scores=[]
        for action in actions :
            ind3=action
            w3,t3,m3,len3,ae3=self.atoms[ind3]
            score=0#m3*self.m_d[0] if m3 is not None else 0
            for model in self.models :
                score+=model(ind1,ind2,ind3,delta*0.1,step)
            fv=(
                (['m3~'+strm(m3),
                #'m3l3~'+strm(m3)+'~'+len3,
                #'m3t3~'+strm(m3)+'~'+t3,
                ] if m3 is not None else [])
                +
                    ([ 'm3m2~'+strm(m3)+'~'+strm(m2), ] if m3 is not None  and m2 is not None else [])+
            [
                    # ok
                    'w3~'+w3, 't3~'+t3, 'l3~'+len3, 'w3t3~'+w3+t3, 'l3t3~'+len3+t3,
                    # ok
                    'w3w2~'+w3+"~"+w2, 'w3t2~'+w3+t2, 't3w2~'+t3+w2, 't3t2~'+t3+t2,

                    'l3w2~'+len3+'~'+w2, 'w3l2~'+w3+'~'+len2, 'l3t2~'+len3+'~'+t2, 't3l2~'+t3+'~'+len2,
                    'l3l2~'+len3+'~'+len2,
                    # ok
                    't3t1~'+t3+'~'+t1, 't3t2t1~'+t3+'~'+t2+'~'+t1,
                    'l3l1~'+len3+'~'+len1, 'l3l2l1~'+len3+'~'+len2+'~'+len1,
                    ])
            """
            fv+=['AE1'+t3+ind for ind in ae3]
            fv+=['AE2'+t2+ind for ind in ae3]
            fv+=['AE3'+t3+ind for ind in ae2]"""
            fvs.append(fv)
            scores.append(score)

        if delta==0 :
            return [[self.weights(fv)+s] for fv,s in zip(fvs,scores)]
        else :
            for fv in fvs :
                self.weights.update_weights(fv,delta,step)
            return [[] for fv in fvs]
        return fvs

    def average_weights(self,step):
        self.weights.average_weights(step)
        for model in self.models:
            model.average_weights(step)

    def un_average_weights(self):
        self.weights.un_average_weights()
        for model in self.models:
            model.un_average_weights()
