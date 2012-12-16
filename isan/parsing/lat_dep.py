import pickle
import json
import collections
import math
from isan.common.lattice import Lattice_Task as Base_Task
from isan.data.lattice import Lattice as Lattice
import isan.parsing.ldep_eval as eval
import isan.data.lattice

def make_color(s,color='36'):
    return '\033['+color+';01m%s\033[1;m'%s #blue


class codec :
    class Json_Lattice_Data :
        def __init__(self,line):
            self.lattice=json.loads(line)
        def make_raw(self):
            lat=self.lattice
            raw=[]
            for i in range(len(lat)):
                k,v =lat[i]
                k=tuple(k)
                lat[i][0]=k
                #if not ('is_test' in v and v['is_test']) :
                if True:
                    raw.append([k,v.get('tag-weight',None)])
                if 'dep' in v and v['dep'][1]!=None :
                    v['dep'][1]=tuple(v['dep'][1])
            l,w=zip(*raw)
            lattice=Lattice(l,w)
            return lattice

        def make_gold(self):
            lat=self.lattice
            gold=[]
            for k,v in lat :
                if 'tag-weight' in v : del v['tag-weight']
                if not v : v=None
                else :
                    v=[v['dep'][1]]
                gold.append([k,v])
            return gold
    @staticmethod
    def decode(line):
        data=codec.Json_Lattice_Data(line)
        lattice=data.make_raw()
        lat=data.make_gold()
        return {'raw':lattice,'y':lat}
    @staticmethod
    def result_to_arcs(result):
        index={}
        arcs=[]
        for i in range(len(result)):
            k,v=result[i]
            index[k]=i
            if v is None : continue
            head=v[0]
            arcs.append((k,head))
        arcs=[(index[a],index[b] if b is not None else -1)for a,b in arcs]
        arcs=sorted(arcs)
        return arcs
    @staticmethod
    def arcs_to_result(arcs,lattice):
        rst=set()
        rst_result=arcs
        std_result=lattice.items
        for s,d in rst_result :
            s=std_result[s]
            d=std_result[d] if d != -1 else None
            r=(s[:3],s[3],d)
            rst.add(r)
        return rst
        pass


class Action :
    _shift_offset=200
    left_reduce=ord('l')
    right_reduce=ord('r')
    @staticmethod
    def shift_action(sind):
        return Action._shift_offset+sind

    @staticmethod
    def parse_action(action):
        if action<Action._shift_offset : 
            return False,
        else :
            return True,action-Action._shift_offset
    @staticmethod
    def actions_to_arcs(actions):
        stack=[]
        arcs=[]
        for a in actions:
            is_shift,*rest=Action.parse_action(a)
            if is_shift :
                ind = rest[0]
                stack.append(ind)
                ind+=1
            elif a==Action.left_reduce:
                arcs.append((stack[-1],stack[-2]))
                stack.pop()
            elif a==Action.right_reduce:
                arcs.append((stack[-2],stack[-1]))
                stack[-2]=stack[-1]
                stack.pop()
        while stack :
            arcs.append((stack.pop(),-1))
        arcs.sort()
        return arcs
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
                    actions.append(Action.left_reduce)
                elif stack[-2][1] == stack[-1][0] :
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                    actions.append(Action.right_reduce)
                else :
                    break
        return actions

class State (Action):
    """
    """

    init_stat=pickle.dumps((0,(0,0),(None,None,None),(None,None)))
    @staticmethod
    def load(bt):
        return pickle.loads(bt)
    def __init__(self,bt,lattice):
        self.lattice=lattice
        state=pickle.loads(bt)
        self.ind,self.span,self.stack_top,self.sequence=state
        self.stop_step=2*self.lattice.length-1
    def shift(self,shift_ind):
        item=self.lattice.items[shift_ind]
        next_ind=self.ind+2*len(item[2])-1
        #next_ind=self.ind+2*len(item[2])
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
    def reduce(self,pre_state,alpha_ind):
        #return []
        next_ind=self.ind+1
        if next_ind==self.stop_step : next_ind=-1
        s0,s1,s2=self.stack_top
        if s0==None or s1==None:return []

        reduce_state1=(
                next_ind,
                (pre_state.span[0],self.span[1]),
                (
                    ( s1[0], s1[1], self.lattice.items[s0[0]][3]),
                    pre_state.stack_top[1],
                    pre_state.stack_top[2]),
                self.sequence
                )
        reduce_state2=(
                next_ind,
                (pre_state.span[0],self.span[1]),
                (
                    (s0[0],self.lattice.items[s1[0]][3],s0[2]),
                    pre_state.stack_top[1],
                    pre_state.stack_top[2]),
                self.sequence
                )
        reduce_state1=pickle.dumps(reduce_state1)
        reduce_state2=pickle.dumps(reduce_state2)
        return [
                (self.left_reduce,next_ind,reduce_state1,alpha_ind),
                (self.right_reduce,next_ind,reduce_state2,alpha_ind),
                ]
    def __str__(self):
        wid0=self.sequence[0]
        wid1=self.sequence[1]
        w0='~'
        w1='~'
        if wid0 is not None and wid0>=0:
            w0=self.lattice.items[wid0]
            w0='%s_%s'%(w0[2],w0[3])
        if wid1 is not None and wid1>=0:
            w1=self.lattice.items[wid1]
            w1='%s_%s'%(w1[2],w1[3])

        ss0,ss1,ss2='~','~','~'
        s0,s1,s2=self.stack_top
        if s0 :
            s0w=self.lattice.items[s0[0]]
            s0w='%s_%s'%(s0w[2],s0w[3])
            ss0=r'%s\%s/%s'%(s0[1],s0w,s0[2])
        if s1 :
            s1w=self.lattice.items[s1[0]]
            s1w='%s_%s'%(s1w[2],s1w[3])
            ss1=r'%s\%s/%s'%(s1[1],s1w,s1[2])
        if s2:
            ss2=s2
        stack="%s %s %s |"%(make_color(ss2,'34'),make_color(ss1,'35'),make_color(ss0))
        return '步数 %d, span (%d,%d) (%s %s] stack: %s'%(
                self.ind,self.span[0],self.span[1],
                make_color(w1,'32'),
                make_color(w0,'33'),
                stack
                )


class Dep (Base_Task):
    name="依存句法分析"
    State=State
    Action=Action
    Eval=eval.Eval
    codec=codec


    def set_raw(self,raw,_):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.lattice=raw
        self.cb_fvs=[]
        for i,item in enumerate(self.lattice.items):
            fv=[b'CBstep' for x in range(2*(item[1]-item[0])-1)]

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
                fv+=[
                        b'C1'+pos+c,
                        b'C2'+pos+l1,
                        b'C3'+pos+r1,
                        b'C4'+pos+l2+l1,
                        b'C5'+pos+l1+c,
                        b'C6'+pos+c+r1,
                        b'C7'+pos+r1+r2,
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
        #print(stat)
        s0,s1,s2_t=stack_top
        s2_t=b'~' if s2_t is None else s2_t.encode()
        if s0:
            s0_ind,s0l_t,s0r_t=s0
            s0l_t=b'~' if s0l_t is None else s0l_t.encode()
            s0r_t=b'~' if s0r_t is None else s0r_t.encode()
            s0_w,s0_t=self.f_raw[s0_ind]
            s0_m=self.margins[s0_ind]
        else:
            s0_w,s0_t,s0l_t,s0r_t=b'~',b'~',b'~',b'~'
            s0_m=b'~'
        if s1:
            s1_ind,s1l_t,s1r_t=s1
            s1l_t=b'~' if s1l_t is None else s1l_t.encode()
            s1r_t=b'~' if s1r_t is None else s1r_t.encode()
            s1_w,s1_t=self.f_raw[s1_ind]
        else:
            s1_w,s1_t,s1l_t,s1r_t=b'~',b'~',b'~',b'~'
        base_fv=[
                b'len'+str(len(s0_w)).encode(),
                #(1)
                b'0'+s0_w,
                b'1'+s0_t,
                b'2'+s0_w+s0_t,
                b'3'+s1_w,
                b'4'+s1_t,
                b'5'+s1_w+s1_t,
                b'9'+s0_w+b":"+s1_w,
                b'0'+s0_t+s1_t,
                b'b'+s0_w+s0_t+s1_t,
                b'c'+s0_t+s1_w+s1_t,
                b'd'+s0_w+s1_t+s1_w,
                b'e'+s0_w+s0_t+s1_w,
                b'f'+s0_w+s0_t+s1_w+s1_t,
                #(4)
                b'k'+s0_t+s1_t+s1l_t,
                b'l'+s0_t+s1_t+s1r_t,
                b'm'+s0_t+s1_t+s0l_t,
                b'n'+s0_t+s1_t+s0r_t,
                b'o'+s0_w+s1_t+s0l_t,
                b'p'+s0_w+s1_t+s0r_t,

                b'6'+qq0,
                b'7'+qq0+qq1,
                #(2)
                b'a'+s0_t+qq0,
                #(3)
                b'h'+s0_t+s1_t+qq0,
                b'j'+s0_w+s1_t+qq0,
                ]

        def _shift_f(stat,sind):
            q0_w,q0_t=self.f_raw[sind]
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
                    #(2)
                    b'a'+s0_t+q0_t,
                    #(3)
                    b'h'+s0_t+s1_t+q0_t,
                    b'j'+s0_w+s1_t+q0_t,
                    ]
            fv+=self.cb_fvs[sind]
            if s0_m :
                fv+=[b'M'+s0_m]
            ba=b'sh'
            fv=[ba+x for x in fv]+[b'SHIFT']
            return fv
            pass
        def _reduce_f(stat,action):
            fv=base_fv[:]
            if s0_m :
                fv+=[b'M'+s0_m]+[b'REDUCE']
            ba=chr(action).encode()
            fv=[ba+x for x in fv]
            return fv

        fvs=[]

        for action in actions:
            is_shift,*rest=self.Action.parse_action(action)
            if is_shift :
                fv=_shift_f(span,rest[0])
            else :
                fv=_reduce_f(span,action)
            fvs.append(fv[:])
        return fvs

