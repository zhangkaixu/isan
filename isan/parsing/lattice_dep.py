import json
import pickle
from isan.common.task import Lattice
from isan.parsing.default_dep import SoftMax, Action
from isan.parsing.default_dep import Dep as Base_Dep

class codec:
    """
    维阿里_NR_1_VMOD 看好_VV_-1_ROOT 欧文_NR_1_VMOD
    """
    @staticmethod
    def decode(line):
        #"""
        line=json.loads(line)
        line=[(tuple(k),m,(tuple(l[0]) if l[0] else -1) if l is not None else None) for k,m,l in line]

        line=[item for item in line if item[2]!=None]

        raw=[(k[0],k[1],(k[2],k[3])) for k,m,l in line]

        #raw=[((k[2],k[3])) for k,m,l in line]
        #raw=[(i,i+1,c) for i,c in enumerate(raw)]

        raw=Lattice(raw)
        inds={}
        for i in range(len(line)):
            inds[line[i][0]]=i
        sen=[(k[2],k[3],inds[l] if l!=-1 else l) for k,m,l in line]
        #print(raw)
        #print(sen)
        #input()
        return {'raw':raw, 'y': sen}
        #"""

        sen=[]
        for arc in line.split():
            word,tag,head_ind,arc_type=arc.rsplit('_',3)
            head_ind=int(head_ind)
            sen.append((word,tag,head_ind,arc_type))
        raw=[(w,t)for w,t,*_ in sen]
        raw=[(i,i+1,c) for i,c in enumerate(raw)]
        raw=Lattice(raw)
        sen=[(w,t,h) for w,t,h,_ in sen]
        print(raw)
        print(sen)
        input()
        return {'raw':raw, 'y': sen }

    @staticmethod
    def encode(y):
        return ' '.join(y)

class State (list) :
    """
    (begin,end),(s0,s1,s2)
    """
    init_state=pickle.dumps(((0,0),(None,None,None)))

    decode=pickle.loads
    encode=pickle.dumps

    def __init__(self,lattice,bt=init_state):
        self.lattice=lattice
        self.extend(pickle.loads(bt))

    def shift(self): # shift
        """
        @return [ (action,state), ... ]
        """
        span,stack_top=self
        pos=span[1]
        nex=self.lattice.begins.get(pos,None) # nex is the list of next items
        if not nex : return []

        s0,s1,s2=stack_top
        # nex[0], nex[1] ...

        rtns=[]
        for ne in nex :
            item=self.lattice[ne]
            ns=((item[0],item[1]),((ne,None,None),s0,s1[0]if s1 else None))
            rtns.append((ord('S'),pickle.dumps(ns)))
        return rtns

    def reduce(self,predictor):
        """
        given predictor
        @return [ (action,state), ... ]
        """
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
class Dep (Base_Dep):
    codec=codec
    State=State

    def shift(self,last_ind,stat):
        state=self.State(self.lattice,stat)

        rtn=[]
        for a,s in state.shift() :
            ss=self.State(self.lattice,s)
            next_ind=last_ind+1
            if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
            rtn.append((a,next_ind,s))
            #print('next',ss)
        
        return rtn

    def reduce(self,last_ind,stat,pred_inds,predictors):
        next_ind=last_ind+1
        if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat)
        rtn=[]
        for i,predictor in enumerate(predictors) :
            rtn+=[(a,next_ind,s,i) for a,s in state.reduce(self.State(self.lattice,predictor))]
        return rtn
