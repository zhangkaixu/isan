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
        
        """
        raw=[((k[2],k[3])) for k,m,l in line]
        raw=[(i,i+1,c) for i,c in enumerate(raw)]
        #"""

        raw=Lattice(raw)
        inds={}
        for i in range(len(line)):
            inds[line[i][0]]=i

        sen=[(k[2],k[3],(inds[l] if l!=-1 else l) if l is not None else None) for k,m,l in line]
        #print(raw)
        #print(sen)
        #input()
        return {'raw':raw, 'y': sen}

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
        # nex[0], nex[1] ...

        s0,s1,s2=stack_top

        print('shift==========', self)
        rtns=[]
        for ne in nex :
            item=self.lattice[ne]
            ns=((item[0],item[1]),((ne,None,None),s0,s1[0]if s1 else None))
            print(ne,ns)
            rtns.append((256+ne,pickle.dumps(ns)))
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

        print('reduce>>>>>>>>',self)

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

        #print('state',state)
        rtn=[]
        for a,s in state.shift() :
            ss=self.State(self.lattice,s)
            diff=(ss[0][1]-ss[0][0])*2-1
            #next_ind=last_ind+diff
            #if next_ind==2*(self.lattice.length)-1 : next_ind=-1 # -1 means the last step

            next_ind=last_ind+1
            if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
            rtn.append((a,next_ind,s))

            #print('next',ss)
        return rtn

    def reduce(self,last_ind,stat,pred_inds,predictors):
        next_ind=last_ind+1
        #if next_ind==2*(self.lattice.length)-1 : next_ind=-1 # -1 means the last step
        if next_ind==2*len(self.lattice)-1 : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat)
        rtn=[]
        for i,predictor in enumerate(predictors) :
            rtn+=[(a,next_ind,s,i) for a,s in state.reduce(self.State(self.lattice,predictor))]
        return rtn

    def set_oracle(self,raw,y) :
        self.oracle={}
        
        self.set_raw(raw,y)
        self.stop_step=None
        std_actions=self.result_to_actions(y)
        #print(std_actions)
        moves=self.actions_to_moves(std_actions,raw)
        #for ind,state,action in moves :
            #print(ind,self.State(self.lattice,state),action)
        #input()

        for step,state,action in moves :
            self.oracle[step]=self.State.decode(state)

        return moves

    """
    Action related
    """
    class Action :
        """
        action : (ind, label)
        act : int
        """
        @staticmethod
        def decode(act):
            if act >= 256 :
                return (act-256,'S')
            else : 
                a=chr(act)
                return (-1,a)

        @staticmethod
        def encode(action):
            if action[1]=='S' :
                return 256+action[0]
            else :
                return ord(action[1])

        @staticmethod
        def shift(ind=0) :
            return (ind,'S')

        @staticmethod
        def reduce(direction):
            return (-1,direction)

    def result_to_actions(self,result):
        result=[r[-1] for r in result]
        stack=[]
        actions=[]
        record=[[ind,head,0] for ind,head in enumerate(result)]# [ind, ind_of_head, 是head的次数]
        for ind,head,_ in record:
            if head!=-1 :
                record[head][2]+=1
        for ind,head in enumerate(result):
            actions.append(self.Action.shift(ind)) # shift
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append(self.Action.reduce('L')) # left reduce, left is the head
                    stack.pop()
                    stack[-1][2]-=1
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append(self.Action.reduce('R'))
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
        input()
        return z

    """
    features
    """
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

        #pos=span[1]
        #q0_w,q0_t=self.f_raw[pos] if pos<len(self.f_raw) else ('~','~')

        fv=[
                #(1)
                '0'+s0_w, '1'+s0_t, '2'+s0_w+s0_t,
                '3'+s1_w, '4'+s1_t, '5'+s1_w+s1_t,
                #'6'+q0_w, '7'+q0_t, '8'+q0_w+q0_t,
                #(2)
                '9'+s0_w+":"+s1_w, '0'+s0_t+s1_t, 
                #'a'+s0_t+q0_t,
                'b'+s0_w+s0_t+s1_t, 'c'+s0_t+s1_w+s1_t,
                'd'+s0_w+s1_t+s1_w, 'e'+s0_w+s0_t+s1_w,
                'f'+s0_w+s0_t+s1_w+s1_t,
                #(3)
                #'h'+s0_t+s1_t+q0_t,
                #'j'+s0_w+s1_t+q0_t,
                #(4)
                'k'+s0_t+s1_t+s1l_t, 'l'+s0_t+s1_t+s1r_t,
                'm'+s0_t+s1_t+s0l_t, 'n'+s0_t+s1_t+s0r_t,
                'o'+s0_w+s1_t+s0l_t, 'p'+s0_w+s1_t+s0r_t,
                #(5)
                'q'+s0_t+s1_t+s2_t,
                ]
        fv=[f for f in fv if '^' not in f]

        

        acts=[x if x <256 else 256 for x in acts]
        fvs=[[action+x for x in fv]for action in map(chr,acts)]

        if delta==0 :
            scores=[[self.weights(fv)] for fv in fvs]
            return scores
        
        else :
            for fv in fvs :
                self.weights.update_weights(fv,delta,step)
            return [[] for fv in fvs]

        return fvs
