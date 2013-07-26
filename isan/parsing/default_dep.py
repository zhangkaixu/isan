import pickle
import random
import isan.parsing.dep_unlabeled_eval as eval
from isan.common.task import Lattice, Base_Task, Early_Stop_Pointwise
import numpy as np
import gzip


class SoftMax :
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
        self.zw=np.zeros(50)
        self.zv=np.zeros(10)
        gz=gzip.open('2to3.gz','rb')

        self.zw=np.array([0.0 for i in range(50)])
        self.zt=np.array([0.0 for i in range(10)])
        self.vw=lambda x : self.words.get(x,self.zw)
        self.vt=lambda x : self.tags.get(x,self.zt)

        self.Ws=[]
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.Ws.append(np.array(pickle.load(gz)))
        self.V=np.array(pickle.load(gz))
        self.b=np.array(pickle.load(gz))
        self.bp=np.array(pickle.load(gz))

        self.d={}
        self.d['S']=np.zeros(100)
        self.d['L']=np.zeros(100)
        self.d['R']=np.zeros(100)
        self.s={k:v.copy()for k,v in self.d.items()}

    def set_raw(self,f_raw):
        self.f_raw=f_raw
        self.s_raw=[]
        for w,t in self.f_raw :
            self.s_raw.append([self.vw(w),self.vt(t)])
        self.s_raw.append([self.zw,self.zt])
        self.s_q0=[]
        self.s_s1=[]
        self.s_s0r=[]
        self.s_s0l=[]
        self.s_s0=[]
        for w,t in self.s_raw :
            self.s_q0.append(np.dot(w,self.Ws[0])+np.dot(t,self.Ws[1]))
            self.s_s0.append(np.dot(w,self.Ws[2])+np.dot(t,self.Ws[3]))
            self.s_s0l.append(np.dot(w,self.Ws[4])+np.dot(t,self.Ws[5]))
            self.s_s0r.append(np.dot(w,self.Ws[6])+np.dot(t,self.Ws[7]))
            self.s_s1.append(np.dot(w,self.Ws[8])+np.dot(t,self.Ws[9]))
            pass
        return


    def __call__(self,sv,acts,scores,delta=0,step=0) :
        if sv[1]==None : sv[1]=-1
        if sv[2]==None : sv[2]=-1
        if sv[3]==None : sv[3]=-1
        if sv[4]==None : sv[4]=-1
        x=(self.b 
                + self.s_q0[sv[0]]
                + self.s_s0[sv[1]]
                + self.s_s0l[sv[2]]
                + self.s_s0r[sv[3]]
                + self.s_s1[sv[4]]
                )

        fv=(np.tanh(x)+1)/2

        if delta==0 :
            for score,act in zip(scores,acts) :
                x=np.dot(self.d[chr(act)],fv)
                score[0]+=x
            return
        else :
            for act in (acts) :
                self.d[chr(act)]+=fv*delta
                self.s[chr(act)]+=fv*(delta*step)
            return
    def average_weights(self,step):
        self._b={}
        for k in self.d :
            self._b[k]=self.d[k].copy()
            #self.d[k]=self.d[k]-self.s[k]/step
            self.d[k]-=self.s[k]/step

    def un_average_weights(self):
        self.d={}
        for k in self._b :
            self.d[k]=self._b[k].copy()


class codec:
    @staticmethod
    def decode(line):
        sen=[]
        for arc in line.split():
            word,tag,head_ind,arc_type=arc.rsplit('_',3)
            head_ind=int(head_ind)
            sen.append((word,tag,head_ind,arc_type))
        raw=[(w,t)for w,t,*_ in sen]
        raw=[(i,i+1,c) for i,c in enumerate(raw)]
        raw=Lattice(raw)
        sen=[(w,t,h) for w,t,h,_ in sen]
        return {'raw':raw, 'y': sen }

    @staticmethod
    def encode(y):
        return ' '.join(y)


class Action :
    """
    action : (ind, label)
    act : int
    """
    @staticmethod
    def decode(act):
        a=chr(act)
        if a=='S' : return (0,'')
        else : return (-1,a)

    @staticmethod
    def encode(action):
        if action[0]==0 :
            return ord('S')
        else :
            return ord(action[1])



class State (list) :
    init_state=pickle.dumps(((0,0),(None,None,None)))

    decode=pickle.loads
    encode=pickle.dumps

    def __init__(self,lattice,bt=init_state):
        self.lattice=lattice
        self.extend(pickle.loads(bt))

    def shift(self):
        span,stack_top=self
        pos=span[1]
        nex=self.lattice.begins.get(pos,None)
        if not nex : return []
        s0,s1,s2=stack_top
        ns=((pos,pos+1),((nex[0],None,None),s0,s1[0]if s1 else None))
        return [( ord('S'), pickle.dumps(ns))]

    def reduce(self,predictor):
        span,stack_top=self
        s0,s1,s2=stack_top
        if s0==None or s1==None:return []
        p_span,pstack=predictor

        rtn= [
             (ord('L'),pickle.dumps(( # ind
                (p_span[0],span[1]), #span
                ((s1[0],s1[1],s0[0]),pstack[1],pstack[2]))), ##
                ),
             (ord('R'),pickle.dumps(( #
                (p_span[0],span[1]),
                ((s0[0],s1[0],s0[2]),pstack[1],pstack[2]))),
                ),
             ]
        return rtn



class Dep (Early_Stop_Pointwise, Base_Task):
    name="依存句法分析"

    codec=codec
    Action=Action
    State=State
    Eval=eval.Eval

    def __init__(self,args=None):
        self.models=[]
        #self.models.append(SoftMax())
        #random.seed(123)
        pass

    def result_to_actions(self,result):
        result=[r[-1] for r in result]
        stack=[]
        actions=[]
        record=[[ind,head,0] for ind,head in enumerate(result)]# [ind, ind_of_head, 是head的次数]
        for ind,head,_ in record:
            if head!=-1 :
                record[head][2]+=1
        for ind,head in enumerate(result):
            actions.append((0,'')) # shift
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append((-1,'L')) # left reduce, left is the head
                    stack.pop()
                    stack[-1][2]-=1
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append((-1,'R'))
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                else:
                    break
        return actions


    def actions_to_result(self,actions):
        ind=0
        stack=[]
        arcs=[]
        for t,l in actions :
            if t>=0:
                stack.append(ind)
                ind+=1
            elif l=='L' :
                arcs.append((stack[-1],stack[-2]))
                stack.pop()
            elif l=='R' :
                arcs.append((stack[-2],stack[-1]))
                stack[-2]=stack[-1]
                stack.pop()
        arcs.append((stack[-1],-1))
        arcs.sort()
        arcs=[x for _,x in arcs]
        z=[]
        for head,it in zip(arcs,self.lattice) :
            z.append(tuple(list(it[2])+[head]))
        return z

    def shift(self,last_ind,stat):
        next_ind=last_ind+1
        if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat,)
        return [(a,next_ind,s) for a,s in state.shift()]

    def reduce(self,last_ind,stat,pred_inds,predictors):
        next_ind=last_ind+1
        if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat,)
        rtn=[]
        for i,predictor in enumerate(predictors) :
            rtn+=[(a,next_ind,s,i) for a,s in state.reduce(self.State(self.lattice,predictor,))]
        return rtn

    def set_oracle(self,raw,y) :
        self.oracle={}
        
        self.set_raw(raw,y)
        self.stop_step=None
        std_actions=self.result_to_actions(y)
        moves=self.actions_to_moves(std_actions,raw)


        for step,state,action in moves :
            self.oracle[step]=self.State.decode(state)

        return moves

    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.lattice=raw
        self.f_raw=[[x[0],x[1]] for b,e,x in self.lattice]

        for model in self.models :
            model.set_raw(self.f_raw)
        if not hasattr(self,'oracle') or not self.oracle : return
        

    def gen_features(self,stat,acts,delta=0,step=0):
        span,stack_top=self.State.decode(stat)
        s0,s1,s2=stack_top

        s2_t='~' if s2 is None else self.f_raw[s2][1]

        if s0:
            s0m,s0l,s0r=s0
            s0l_t='~' if s0l is None else self.f_raw[s0l][1]
            s0r_t='~' if s0r is None else self.f_raw[s0r][1]
            s0l_w='~' if s0l is None else self.f_raw[s0l][0]
            s0r_w='~' if s0r is None else self.f_raw[s0r][0]
            s0_w,s0_t=self.f_raw[s0m]
        else:
            s0m,s0l,s0r=-1,-1,-1
            s0_w,s0_t,s0l_t,s0r_t='~','~','~','~'
            s0l_w,s0r_w='~','~'

        if s1:
            s1m,s1l,s1r=s1
            s1l_t='~' if s1l is None else self.f_raw[s1l][1]
            s1r_t='~' if s1r is None else self.f_raw[s1r][1]
            s1_w,s1_t=self.f_raw[s1m]
        else:
            s1_w,s1_t,s1l_t,s1r_t='~','~','~','~'
            s1m=-1

        pos=span[1]
        q0_w,q0_t=self.f_raw[pos] if pos<len(self.f_raw) else ('~','~')
        q1_t=self.f_raw[pos+1][1] if pos+1<len(self.f_raw) else '~'

        fv=[
                #(1)
                '0'+s0_w, '1'+s0_t, '2'+s0_w+s0_t,
                '3'+s1_w, '4'+s1_t, '5'+s1_w+s1_t,
                '6'+q0_w, '7'+q0_t, '8'+q0_w+q0_t,
                #(2)
                '9'+s0_w+":"+s1_w, '0'+s0_t+s1_t, 'a'+s0_t+q0_t,
                'b'+s0_w+s0_t+s1_t, 'c'+s0_t+s1_w+s1_t,
                'd'+s0_w+s1_t+s1_w, 'e'+s0_w+s0_t+s1_w,
                'f'+s0_w+s0_t+s1_w+s1_t,
                #(3)
                'g'+s0_t+q0_t+q1_t, 'h'+s0_t+s1_t+q0_t,
                'i'+s0_w+q0_t+q1_t, 'j'+s0_w+s1_t+q0_t,
                #(4)
                'k'+s0_t+s1_t+s1l_t, 'l'+s0_t+s1_t+s1r_t,
                'm'+s0_t+s1_t+s0l_t, 'n'+s0_t+s1_t+s0r_t,
                'o'+s0_w+s1_t+s0l_t, 'p'+s0_w+s1_t+s0r_t,
                #(5)
                'q'+s0_t+s1_t+s2_t,
                ]
        fv=[f for f in fv if '^' not in f]

        fvs=[[action+x for x in fv]for action in map(chr,acts)]

        if delta==0 :
            scores=[[self.weights(fv)] for fv in fvs]
            for model in self.models :
                model([pos,s0m,s0l,s0r,s1m],acts,scores)
            return scores
        
        else :
            for fv in fvs :
                self.weights.update_weights(fv,delta,step)
            for model in self.models :
                model([pos,s0m,s0l,s0r,s1m],acts,None,delta*0.1,step)
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
