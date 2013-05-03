import pickle
import isan.parsing.dep_unlabeled_eval as eval
from isan.common.task import Lattice, Base_Task, Early_Stop_Pointwise

import time

class Times (dict) :
    def __call__(self,key):
        if key not in self :
            self[key]=[0,None]
        data=self[key]
        if data[1]==None :
            data[1]=time.time()
        else :
            data[0]+=time.time()-data[1]
            data[1]=None
    def __repr__(self):
        return '\n'.join(str(k)+":"+str(v[0]) for k,v in self.items())

times=Times()

class codec:
    @staticmethod
    def decode(line):
        sen=[]
        for arc in line.split():
            word,tag,head_ind,arc_type=arc.split('_')
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
    @staticmethod
    def decode(action):
        a=chr(action)
        if a=='S' : return (0,'')
        else : return (-1,a)

    @staticmethod
    def encode(action):
        if action[0]==0 :
            return ord('S')
        else :
            return ord(action[1])



class State (list) :
    init_stat=pickle.dumps(((0,0),(None,None,None)))
    @staticmethod
    def load(bt):
        return pickle.loads(bt)

    def __init__(self,lattice,bt=init_stat):
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
    def dumps(self):
        return pickle.dumps(tuple(self))



class Dep (Early_Stop_Pointwise, Base_Task):
    name="依存句法分析"

    Action=Action
    State=State
    Eval=eval.Eval
    codec=codec

    def report(self):
        print(times)

    def get_init_states(self) :
        return [self.State.init_stat]

    def shift(self,last_ind,stat):
        next_ind=last_ind+1
        if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat,)
        return [(a,next_ind,s) for a,s in state.shift()]

    def reduce(self,last_ind,stat,pred_inds,predictors):
        next_ind=last_ind+1
        if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat,)
        rtn2=[]
        for i,predictor in enumerate(predictors) :
            rtn2+=[(a,next_ind,s,i) for a,s in state.reduce(self.State(self.lattice,predictor,))]
        return rtn2
    
    def __init__(self):
        # autoencoder
        #self.ae={}
        #for line in open("large.50.99.txt"):
        #for line in open("/home/zkx/wordtype/autoencoder/top4.txt"):
        #for line in open("/home/zkx/wordclass/dict.txt"):
        #for line in open("/home/zkx/wordtype/autoencoder/70words.9.txt"):
        #    word,*inds=line.split()
        #for line in open("/home/zkx/brown-cluster/011-c500-p1-Rwords_1000.out/paths"):
        #    inds,word,*_=line.split()
        #    inds=[inds]
        #    inds=[x.encode() for x in inds]
        #    self.ae[word]=inds
        pass

    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.lattice=raw
        self.f_raw=[[x[0].encode()if x[0] else b'',x[1].encode()if x[1] else b''] for b,e,x in self.lattice]

        # autoencoder
        #self.ae_inds=[]
        #for word,tag in raw :
        #    #if tag[0]!='N' :
        #    #    self.ae_inds.append([])
        #    #    continue
        #    if len(word)==1 :
        #        self.ae_inds.append([b'**'])
        #    else:
        #        self.ae_inds.append(self.ae.get(word,[b'*']))
        #print(len(self.ae))
        #print(raw)
        #print(self.ae_inds)
        #input()

    def gen_features(self,span,actions):
        fvs=[]
        fv=self.gen_features_one(span)
        for action in actions:
            action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

    def gen_features_one(self,stat):
        stat=pickle.loads(stat)
        span,stack_top=stat
        s0,s1,s2=stack_top

        s2_t=b'~' if s2 is None else self.f_raw[s2][1]

        if s0:
            s0m,s0l,s0r=s0
            s0l_t=b'~' if s0l is None else self.f_raw[s0l][1]
            s0r_t=b'~' if s0r is None else self.f_raw[s0r][1]
            s0_w=self.f_raw[s0m][0]
            s0_t=self.f_raw[s0m][1]
            #aeind0h=self.ae_inds[s0m]
        else:
            s0_w,s0_t,s0l_t,s0r_t=b'~',b'~',b'~',b'~'
            #aeind0h=[]

        if s1:
            s1m,s1l,s1r=s1
            s1l_t=b'~' if s1l is None else self.f_raw[s1l][1]
            s1r_t=b'~' if s1r is None else self.f_raw[s1r][1]
            s1_w=self.f_raw[s1m][0]
            s1_t=self.f_raw[s1m][1]
        else:
            s1_w,s1_t,s1l_t,s1r_t=b'~',b'~',b'~',b'~'

        q0_w,q0_t=self.f_raw[span[1]] if span[1]<len(self.f_raw) else (b'~',b'~')
        q1_t=self.f_raw[span[1]+1][1] if span[1]+1<len(self.f_raw) else b'~'

        fv=[
                #(1)
                b'0'+s0_w, b'1'+s0_t, b'2'+s0_w+s0_t,
                b'3'+s1_w, b'4'+s1_t, b'5'+s1_w+s1_t,
                b'6'+q0_w, b'7'+q0_t, b'8'+q0_w+q0_t,
                #(2)
                b'9'+s0_w+b":"+s1_w, b'0'+s0_t+s1_t, b'a'+s0_t+q0_t,
                b'b'+s0_w+s0_t+s1_t, b'c'+s0_t+s1_w+s1_t,
                b'd'+s0_w+s1_t+s1_w, b'e'+s0_w+s0_t+s1_w,
                b'f'+s0_w+s0_t+s1_w+s1_t,
                #(3)
                b'g'+s0_t+q0_t+q1_t, b'h'+s0_t+s1_t+q0_t,
                b'i'+s0_w+q0_t+q1_t, b'j'+s0_w+s1_t+q0_t,
                #(4)
                b'k'+s0_t+s1_t+s1l_t, b'l'+s0_t+s1_t+s1r_t,
                b'm'+s0_t+s1_t+s0l_t, b'n'+s0_t+s1_t+s0r_t,
                b'o'+s0_w+s1_t+s0l_t, b'p'+s0_w+s1_t+s0r_t,
                #(5)
                b'q'+s0_t+s1_t+s2_t,
                ]

        # autoencoder
        #for aeind in aeind0h :
        #    fv+=[
        #            b's0_taeind0:'+q0_t+b':'+aeind,
        #            b's0_waeind0:'+q0_w+b':'+aeind,
        #            b's0lt_taeind0:'+s0l_t+b':'+aeind,
        #            b's0rt_taeind0:'+s0r_t+b':'+aeind,
        #            b's1t_taeind0:'+s1_t+b':'+aeind,
        #            b's1w_taeind0:'+s1_w+b':'+aeind,
        #            ]
        return fv




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
        for t,l in actions:
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

