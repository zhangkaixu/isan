import pickle
import json
import collections
import math
from isan.common.lattice import Lattice_Task as Base_Task
from isan.data.lattice import Lattice as Lattice
import isan.parsing.ldep_eval as eval
import isan.data.lattice

from isan.parsing.lat_dep import codec as Base_Codec
from isan.parsing.lat_dep import Action as Action
from isan.parsing.lat_dep import State as State
from isan.parsing.lat_dep import Dep as Base_Dep



class codec (Base_Codec):
    class Json_Lattice_Data :
        def __init__(self,line):
            self.lattice=json.loads(line)
            self.lattice=[[k,v] for k,v in self.lattice if 'dep' in v]
        def make_raw(self):
            lat=self.lattice
            raw=[]
            for i in range(len(lat)):
                k,v =lat[i]
                k=tuple(k)
                lat[i][0]=k
                #if not ('is_test' in v and v['is_test']) :
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


class Dep (Base_Dep):
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
        
        qid=self.lattice.begins.get(sp[1],[len(self.f_raw)])[0]

        q0_w,q0_t=b'~',b'~'
        if qid< len(self.f_raw) :
            q0_w,q0_t=self.f_raw[qid]
        q1_w,q1_t=b'~',b'~'
        if qid+1< len(self.f_raw) :
            q1_w,q1_t=self.f_raw[qid+1]

        w0_w,w0_t=b'~',b'~'
        w1_w,w1_t=b'~',b'~'
        if sequence[0]!=None :
            w0_w,w0_t=self.f_raw[sequence[0]]
        if sequence[1]!=None :
            w1_w,w1_t=self.f_raw[sequence[1]]

        #print(w1_w.decode(),w0_w.decode(),q0_w.decode(),q1_w.decode())

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
                #(1)
                b'0'+s0_w,
                b'1'+s0_t,
                b'2'+s0_w+s0_t,
                b'3'+s1_w,
                b'4'+s1_t,
                b'5'+s1_w+s1_t,
                #(2)
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
                b'q'+s0_t+s1_t+s2_t,

                #b'6~'+qq0,
                #b'7~'+qq0+qq1,
                ##(2)
                #b'a~'+s0_t+qq0,
                #b'a~~'+s0_t+qq0+qq1,
                ##(3)
                #b'i~'+s0_w+qq0,
                #b'h~'+s0_t+s1_t+qq0,
                #b'h~~'+s0_t+s1_t+qq0+qq1,
                #b'j~'+s0_w+s1_t+qq0,


                b'7'+q0_t,
                b'8'+q0_w+q0_t,
                b'a'+s0_t+q0_t,
                b'g'+s0_t+q0_t+q1_t,
                b'h'+s0_t+s1_t+q0_t,
                b'i'+s0_w+q0_t+q1_t,
                b'j'+s0_w+s1_t+q0_t,

                ]

        def _shift_f(stat,sind):
            #q0_w,q0_t=self.f_raw[sind]
            #q0_m=self.margins[sind]
            fv=base_fv[:]
            ba=b'sh'
            fv=[ba+x for x in fv]
            return fv
            pass
        def _reduce_f(stat,action):
            fv=base_fv[:]
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

