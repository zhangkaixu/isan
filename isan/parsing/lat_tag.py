import pickle
import json
import collections
import math
from isan.common.lattice import Lattice_Task as Base_Task
from isan.data.lattice import Lattice as Lattice
import isan.parsing.ldep_eval as eval
import isan.data.lattice

from isan.parsing.lat_dep import codec as codec
from isan.parsing.lat_dep import Action as Base_Action
from isan.parsing.lat_dep import State as Base_State
from isan.parsing.lat_dep import Dep as Base_Dep

class Action (Base_Action):
    @staticmethod
    def arcs_to_actions(arcs):
        is_leaf=collections.Counter()
        for a,b in arcs:
            is_leaf[b]+=1
        stack=[]
        actions=[]
        for i,h in arcs:
            stack.append([i,h,is_leaf[i]])
            actions.append(Action.shift_action(i))
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]==stack[-2][0] :
                    stack.pop()
                    stack[-1][2]-=1
                    #actions.append(Action.left_reduce)
                elif stack[-2][1] == stack[-1][0] :
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                    #actions.append(Action.right_reduce)
                else :
                    break
        return actions

class State (Action,Base_State):
    """
    """

    def __init__(self,bt,lattice):
        self.lattice=lattice
        state=pickle.loads(bt)
        self.ind,self.span,self.stack_top,self.sequence=state
        #self.stop_step=2*self.lattice.length-1
        self.stop_step=2*self.lattice.length
    def shift(self,shift_ind):
        item=self.lattice.items[shift_ind]
        #next_ind=self.ind+2*len(item[2])-1
        next_ind=self.ind+2*len(item[2])
        if next_ind==self.stop_step : next_ind=-1
        state=(
                next_ind,
                (item[0],item[1]),
                (
                    (shift_ind,None,None),
                    self.stack_top[0],
                    self.lattice.items[self.stack_top[1][0]][3] if self.stack_top[1] else None
                ),
                (shift_ind,self.sequence[0]),
            )
        return [(self.shift_action(shift_ind),next_ind,pickle.dumps(state))]


class Dep (Base_Dep):
    name="依存句法分析"
    State=State
    Action=Action
    Eval=eval.Eval
    codec=codec
    reduce=None


    def set_raw(self,raw,_):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.lattice=raw
        self.cb_fvs=[]
        for i,item in enumerate(self.lattice.items):
            fv=[]

            for j,c in enumerate(item[2]):

                o=item[0]+j
                if item[0]+1==item[1]:
                    pos=b's'
                elif o == item[0] :
                    pos=b'b'
                elif o==item[1]-1 :
                    pos=b'e'
                else :
                    pos=b'm'
                l2=self.lattice.sentence[o-2] if o-2>=0 else '#'
                l1=self.lattice.sentence[o-1] if o-1>=0 else '#'
                r1=self.lattice.sentence[o+1] if o+1<len(self.lattice.sentence) else '#'
                r2=self.lattice.sentence[o+2] if o+2<len(self.lattice.sentence) else '#'
                c=c.encode()
                l1=l1.encode()
                l2=l2.encode()
                r1=r1.encode()
                r2=r2.encode()
                tag=item[3].encode()
                fv+=[
                        b'C1'+pos+c,
                        b'C2'+pos+l1,
                        b'C3'+pos+r1,
                        b'C4'+pos+l2+l1,
                        b'C5'+pos+l1+c,
                        b'C6'+pos+c+r1,
                        b'C7'+pos+r1+r2,
                        b'CT1'+pos+c+tag,
                        b'CT2'+pos+l1+tag,
                        b'CT3'+pos+r1+tag,
                        b'CT4'+pos+l2+l1+tag,
                        b'CT5'+pos+l1+c+tag,
                        b'CT6'+pos+c+r1+tag,
                        b'CT7'+pos+r1+r2+tag,
                        ]
            self.cb_fvs.append(fv)
        self.margins=[str(math.floor(math.log(float(k)/64.0+1))).encode() if k!=None else None 
                for k in self.lattice.weights]
        
        self.f_raw=[[k[2].encode(),k[3].encode()] for k in self.lattice.items]

    def gen_features(self,span,actions):
        stat=self.State.load(span)
        ind,sp,stack_top,sequence=stat
        b,e=sp
        qq0=self.lattice.sentence[e].encode() if e < len(self.lattice.sentence) else b'#'
        qq1=self.lattice.sentence[e+1].encode() if e+1 < len(self.lattice.sentence) else b'#'

        w0_w,w0_t=b'~',b'~'
        w1_w,w1_t=b'~',b'~'
        if sequence[0]!=None :
            w0_w,w0_t=self.f_raw[sequence[0]]
        if sequence[1]!=None :
            w1_w,w1_t=self.f_raw[sequence[1]]

        def _shift_f(stat,sind):
            q0_w,q0_t=self.f_raw[sind]
            q0_m=self.margins[sind]
            fv=[
                    b'S0'+w0_w,
                    b'S1'+w0_t,
                    b'S2'+w0_w+b'~'+w0_t,
                    b'S3'+w0_w+b'~'+w1_w,
                    b'S4'+w0_w+b'~'+w1_t,
                    b'S5'+w0_t+b'~'+w1_w,
                    b'S6'+w0_t+b'~'+w1_t,
                    b'S7'+w0_w+b'~'+q0_w,
                    b'S8'+w0_w+b'~'+q0_t,
                    b'S9'+w0_t+b'~'+q0_w,
                    b'Sa'+w0_t+b'~'+q0_t,
                    b'Sb'+w1_t+b'~'+w0_t+b'~'+q0_t,

                    b'6'+q0_w,
                    b'7'+q0_t,
                    b'8'+q0_w+q0_t,
                    ]
            fv+=self.cb_fvs[sind]
            if q0_m : fv+=[b'M'+q0_m]
            ba=b'sh'
            fv=[ba+x for x in fv]
            return fv
            pass

        fvs=[]

        for action in actions:
            rt=self.Action.parse_action(action)
            fv=_shift_f(span,rt[1])
            fvs.append(fv[:])
        return fvs

