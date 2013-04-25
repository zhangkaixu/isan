import pickle
#import marshal as pickle
import isan.parsing.dep_codec as codec
import isan.parsing.eval as eval
from isan.common.lattice import Lattice_Task as Base_Task
from isan.common.lattice import Reenter_Stop as Reenter_Stop

class Lattice :
    def __init__(self,l,w):
        self.weights=w
        self.items=l
        self.length=len(l)
        self.begins={}
        for i in range(len(l)):
            self.begins[i]=[i]

class Action :
    shift_action=ord('s')
    left_reduce=ord('l')
    right_reduce=ord('r')

    @staticmethod
    def parse_action(action):
        if action!=Action.shift_action : 
            return False,
        else :
            return True,None

    @staticmethod
    def actions_to_arcs(actions):
        ind=0
        stack=[]
        arcs=[]
        for a in actions:
            if a==Action.shift_action:
                stack.append(ind)
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
            actions.append(Action.shift_action)
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

class State (Action) :
    init_stat=pickle.dumps((0,(0,0),(None,None,None)))
    @staticmethod
    def load(bt):
        return pickle.loads(bt)

    def __init__(self,bt,lattice):
        self.lattice=lattice
        self.stat=pickle.loads(bt)
        self.stop_step=2*self.lattice.length-1
        ind,self.span,stack_top=self.stat

    def shift(self,_):
        ind,span,stack_top=self.stat
        next_ind=ind+1
        if next_ind==self.stop_step : next_ind=-1
        state=(
                next_ind,
                (span[1],span[1]+1), # stack top 的 span
                ((span[1],None,None),
                        stack_top[0],
                        stack_top[1][0] if stack_top[1] else None)
            )
        return [(State.shift_action, next_ind, pickle.dumps(state))]

    def reduce(self,pre_state,alpha_ind):
        ind,span,stack_top=self.stat
        predictor=pre_state.stat
        s0,s1,s2=stack_top
        if s0==None or s1==None:return []
        assert(predictor[2][0]==s1)
        _,p_span,_=predictor

        next_ind=ind+1
        if next_ind==self.stop_step : next_ind=-1

        rtn= [
             (self.left_reduce,next_ind,pickle.dumps((ind+1, # ind
                (p_span[0],span[1]), #span
                ((s1[0],s1[1],s0[0]),predictor[2][1],predictor[2][2]))), ##
                alpha_ind),
             (self.right_reduce,next_ind,pickle.dumps((ind+1, #
                (p_span[0],span[1]),
                ((s0[0],s1[0],s0[2]),predictor[2][1],predictor[2][2]))),
                alpha_ind),
             ]
        return rtn


class Dep (Reenter_Stop, Base_Task):
    name="依存句法分析"

    Action=Action
    State=State
    Eval=eval.Eval
    codec=codec
    
    def __init__(self):
        # autoencoder
        #self.ae={}
        ##for line in open("large.50.99.txt"):
        #for line in open("/home/zkx/wordtype/autoencoder/top4.txt"):
        ##for line in open("/home/zkx/wordtype/autoencoder/70words.9.txt"):
        #    word,*inds=line.split()
        #    inds=[x.encode() for x in inds]
        #    self.ae[word]=inds
        pass

    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.lattice=Lattice(raw,None)
        self.raw=raw
        self.f_raw=[[w.encode()if w else b'',t.encode()if t else b''] for w,t in raw]

        # autoencoder
        #self.ae_inds=[]
        #for word,tag in raw :
        #    if len(word)==1 :
        #        self.ae_inds.append([b'**'])
        #    else:
        #        self.ae_inds.append(self.ae.get(word,[b'*']))

    def gen_features(self,span,actions):
        fvs=[]
        fv=self.gen_features_one(span)
        for action in actions:
            action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

    def gen_features_one(self,stat):
        stat=pickle.loads(stat)
        ind,span,stack_top=stat
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

        # autoencoder
        #for aeind in aeind0h :
        #    fv+=[
        #            b's0_taeind0~'+q0_t+b'~'+aeind,
        #            b's0_waeind0~'+q0_w+b'~'+aeind,
        #            #b's0lt_taeind0~'+s0l_t+b'~'+aeind,
        #            #b's0rt_taeind0~'+s0r_t+b'~'+aeind,
        #            b's1t_taeind0~'+s1_t+b'~'+aeind,
        #            b's1w_taeind0~'+s1_w+b'~'+aeind,
        #            ]
        return fv

