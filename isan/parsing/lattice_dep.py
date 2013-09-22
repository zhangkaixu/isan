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
        sen=[]
        for arc in line.split():
            word,tag,head_ind,arc_type=arc.rsplit('_',3)
            head_ind=int(head_ind)
            sen.append((word,tag,head_ind,arc_type))
        raw=[(w,t)for w,t,*_ in sen]
        raw=[(i,i+1,c) for i,c in enumerate(raw)]
        raw=Lattice(raw)
        sen=[(w,t,h) for w,t,h,_ in sen]
        #print(sen)
        #input()
        return {'raw':raw, 'y': sen }

    @staticmethod
    def encode(y):
        return ' '.join(y)

class State (list) :
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
        ns=((pos,pos+1),((nex[0],None,None),s0,s1[0]if s1 else None))
        return [(ord('S'), pickle.dumps(ns))]

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
