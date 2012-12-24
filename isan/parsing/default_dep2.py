import pickle
import json
#import marshal as pickle
import isan.parsing.eval as eval
from isan.data.lattice import Lattice as Lattice
from isan.common.lattice import Lattice_Task as Base_Task

from isan.parsing.lat_dep import Action as Base_Action
from isan.parsing.lat_dep import State as Base_State
from isan.parsing.lat_dep import codec as base_codec
from isan.parsing.lat_dep import Dep as Base_Dep


class codec (base_codec):
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
    def arcs_to_result(arcs,lattice):
        return arcs
    @staticmethod
    def result_to_arcs(result):
        result=[ind for _,_,ind,_ in result]
        return result
    @staticmethod
    def encode(raw,result):
        return ' '.join(['_'.join([item[0],item[1],str(head)]) for item,head in zip(raw,result)])

    @staticmethod
    def decode(line):
        data=codec.Json_Lattice_Data(line)
        lattice=data.make_raw()
        lat=data.make_gold()
        #raw=[(w,t)for b,e,w,t in lattice.items]
        raw=lattice
        inds={}
        for i,it in enumerate(lat):
            inds[it[0]]=i
        lat=[tuple([word[2],word[3]]+([inds[head[0]],'DEP'] if head[0] else [-1,'ROOT']))
                for word,head in lat]
        return {'raw':raw,'y':lat}

    @staticmethod
    def to_raw(line):
        return [(w,t)for w,t,*_ in line]

class Action (Base_Action):
    @staticmethod
    def actions_to_arcs(actions):
        ind=0
        stack=[]
        arcs=[]
        for a in actions:
            is_shift,*rest=Action.parse_action(a)
            if is_shift :
                sind=rest[0]
                stack.append(sind)
                ind+=1
            elif a==Action.left_reduce:
                arcs.append((stack[-1],stack[-2]))
                stack.pop()
            elif a==Action.right_reduce:
                arcs.append((stack[-2],stack[-1]))
                stack[-2]=stack[-1]
                stack.pop()
        arcs.append((stack[-1],-1))
        arcs.sort()
        arcs=[x for _,x in arcs]
        return arcs
    @staticmethod
    def arcs_to_actions(arcs):
        result=arcs
        stack=[]
        actions=[]
        record=[[ind,head,0] for ind,head in enumerate(result)]# [ind, ind_of_head, 是head的次数]
        for ind,head,_ in record:
            if head!=-1 :
                record[head][2]+=1
        for ind,head in enumerate(result):
            #actions.append(self.shift_action)
            actions.append(Action.shift_action(ind))
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append(Action.left_reduce)
                    stack.pop()
                    stack[-1][2]-=1
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append(Action.right_reduce)
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                else:
                    break

        return actions

class State(Action,Base_State) :
    init_stat=pickle.dumps((0,(0,0),(None,None,None)))
    def __init__(self,bt,lattice):
        self.lattice=lattice
        state=pickle.loads(bt)
        self.ind,self.span,self.stack_top=state
        #self.stop_step=2*len(self.lattice.items)-1
        self.stop_step=2*self.lattice.length-1

    def shift(self,shift_ind):
        item=self.lattice.items[shift_ind]
        #next_ind=self.ind+1
        next_ind=self.ind+2*len(item[2])-1
        if next_ind==self.stop_step : next_ind=-1

        state=(
                next_ind,
                (item[0],item[1]),
                ((item[2],item[3],None,None),
                        self.stack_top[0],
                        self.stack_top[1][1] if self.stack_top[1] else None)
                )
        return [(self.shift_action(shift_ind),next_ind,pickle.dumps(state))]
        pass
    def reduce(self,pre_state,alpha_ind):
        next_ind=self.ind+1
        if next_ind==self.stop_step : next_ind=-1
        s0,s1,s2=self.stack_top
        if s0==None or s1==None: return []
        reduce_state1=(
                next_ind, 
                (pre_state.span[0],self.span[1]), 
                ((s1[0],s1[1],s1[2],s0[1]),pre_state.stack_top[1],pre_state.stack_top[2]))

        reduce_state2=(next_ind,
                (pre_state.span[0],self.span[1]),
                ((s0[0],s0[1],s1[1],s0[3]),pre_state.stack_top[1],pre_state.stack_top[2]))

        reduce_state1=pickle.dumps(reduce_state1)
        reduce_state2=pickle.dumps(reduce_state2)
        return [
                (self.left_reduce,next_ind,reduce_state1,alpha_ind),
                (self.right_reduce,next_ind,reduce_state2,alpha_ind),
                ]

class Dep (Base_Dep):
    pass

class XX:
    name="依存句法分析"
    Action=Action
    State=State

    Eval=eval.Eval
    codec=codec


    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.lattice=raw
        self.f_raw=[[w.encode()if w else b'',t.encode()if t else b''] 
                for b,e,w,t in self.lattice.items]

    def gen_features(self,span,actions):
        fvs=[]
        fv=self.gen_features_one(span)
        for action in actions:
            is_shift,*_=self.Action.parse_action(action)
            if is_shift :
                action='s'.encode()
            else :
                action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

    def gen_features_one(self,stat):
        stat=State.load(stat)
        _,span,stack_top=stat
        s0,s1,s2_t=stack_top

        s2_t=b'~' if s2_t is None else s2_t.encode()

        if s0:
            s0_w,s0_t,s0l_t,s0r_t=s0
            s0l_t=b'~' if s0l_t is None else s0l_t.encode()
            s0r_t=b'~' if s0r_t is None else s0r_t.encode()
            s0_w=s0_w.encode()
            s0_t=s0_t.encode()
        else:
            s0_w,s0_t,s0l_t,s0r_t=b'~',b'~',b'~',b'~'

        if s1:
            s1_w,s1_t,s1l_t,s1r_t=s1
            s1l_t=b'~' if s1l_t is None else s1l_t.encode()
            s1r_t=b'~' if s1r_t is None else s1r_t.encode()
            s1_w=s1_w.encode()
            s1_t=s1_t.encode()
        else:
            s1_w,s1_t,s1l_t,s1r_t=b'~',b'~',b'~',b'~'

        ind=self.lattice.begins.get(span[1],[len(self.f_raw)])[0]
        q0_w,q0_t=self.f_raw[ind] if ind<len(self.f_raw) else (b'~',b'~')
        q1_t=self.f_raw[ind+1][1] if ind+1<len(self.f_raw) else b'~'
        
        fv=[
                #(1)
                b'0'+s0_w,
                b'1'+s0_t,
                b'2'+s0_w+s0_t,
                b'3'+s1_w,
                b'4'+s1_t,
                b'5'+s1_w+s1_t,
                b'6'+q0_w,
                b'7'+q0_t,
                b'8'+q0_w+q0_t,
                #(2)
                b'9'+s0_w+b":"+s1_w,
                b'0'+s0_t+s1_t,
                b'a'+s0_t+q0_t,
                b'b'+s0_w+s0_t+s1_t,
                b'c'+s0_t+s1_w+s1_t,
                b'd'+s0_w+s1_t+s1_w,
                b'e'+s0_w+s0_t+s1_w,
                b'f'+s0_w+s0_t+s1_w+s1_t,
                #(3)
                b'g'+s0_t+q0_t+q1_t,
                b'h'+s0_t+s1_t+q0_t,
                b'i'+s0_w+q0_t+q1_t,
                b'j'+s0_w+s1_t+q0_t,
                #(4)
                b'k'+s0_t+s1_t+s1l_t,
                b'l'+s0_t+s1_t+s1r_t,
                b'm'+s0_t+s1_t+s0l_t,
                b'n'+s0_t+s1_t+s0r_t,
                b'o'+s0_w+s1_t+s0l_t,
                b'p'+s0_w+s1_t+s0r_t,
                #(5)
                b'q'+s0_t+s1_t+s2_t,
                ]
        return fv
