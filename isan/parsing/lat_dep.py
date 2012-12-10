import pickle
import json
import collections
import math

#import marshal as pickle
import isan.parsing.ldep_eval as eval

def make_color(s,color='36'):
    return '\033['+color+';01m%s\033[1;m'%s #blue

class Dep:
    name="依存句法分析"

    def __init__(self):
        self.Y=None
    
    shift_offset=200
    left_reduce=ord('l')
    right_reduce=ord('r')

    def check(self,std_moves,rst_moves):
        #print('std')
        #for step,state,action in std_moves:
        #    print(step,self.State(state,self),action)
        #print('rst')
        #for step,state,action in rst_moves:
        #    print(step,self.State(state,self),action)

        if len(std_moves)!=len(rst_moves) :return False
        return all(
                std_move[2]==rst_move[2]
                for std_move,rst_move in zip(std_moves,rst_moves)
                )

    def init(self):
        pass
    init_stat=pickle.dumps((0,(0,0),(None,None,None),(None,None)))
    def get_init_states(self) :
        return [self.init_stat]
    Eval=eval.Eval

    class codec :
        @staticmethod
        def decode(line):
            lat=json.loads(line)
            raw=[]
            for i in range(len(lat)):
                k,v =lat[i]
                k=tuple(k)
                lat[i][0]=k
                if not ('is_test' in v and v['is_test']) :
                #if True:
                    raw.append([k,v.get('tag-weight',None)])
                
                if 'dep' in v and v['dep'][1]!=None :
                    v['dep'][1]=tuple(v['dep'][1])
            #print(raw)
            #print(lat)
            #input()
            return {'raw':raw,'y':lat}

    class State :
        def __init__(self,bt,task):
            state=pickle.loads(bt)
            self.task=task
            self.ind,self.span,self.stack_top,self.sequence=state
        def __str__(self):
            wid0=self.sequence[0]
            wid1=self.sequence[1]
            w0='~'
            w1='~'
            if wid0 is not None and wid0>=0:
                w0=self.task.lattice.items[wid0]
                w0='%s_%s'%(w0[2],w0[3])
            if wid1 is not None and wid1>=0:
                w1=self.task.lattice.items[wid1]
                w1='%s_%s'%(w1[2],w1[3])

            ss0,ss1,ss2='~','~','~'
            s0,s1,s2=self.stack_top
            if s0 :
                s0w=self.task.lattice.items[s0[0]]
                s0w='%s_%s'%(s0w[2],s0w[3])
                ss0=r'%s\%s/%s'%(s0[1],s0w,s0[2])
            if s1 :
                s1w=self.task.lattice.items[s1[0]]
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
        def shift(self,task,shift_ind):
            item=task.lattice.items[shift_ind]
            next_ind=self.ind+2*len(item[2])-1
            if next_ind==task.stop_step : next_ind=-1
            state=(
                    next_ind,
                    (item[0],item[1]),
                    (
                        (shift_ind,None,None),
                        self.stack_top[0],
                        task.lattice.items[self.stack_top[1][0]][3] if self.stack_top[1] else None
                    ),
                    (shift_ind,self.sequence[0]),

                )
            return [(shift_ind+task.shift_offset,next_ind,pickle.dumps(state))]
        def reduce(self,task,pre_state,alpha_ind):
            next_ind=self.ind+1
            if next_ind==task.stop_step : next_ind=-1
            s0,s1,s2=self.stack_top
            if s0==None or s1==None:return []

            reduce_state1=(
                    next_ind,
                    (pre_state.span[0],self.span[1]),
                    (
                        ( s1[0], s1[1], task.lattice.items[s0[0]][3]),
                        pre_state.stack_top[1],
                        pre_state.stack_top[2]),
                    self.sequence
                    )
            reduce_state2=(
                    next_ind,
                    (pre_state.span[0],self.span[1]),
                    (
                        (s0[0],task.lattice.items[s1[0]][3],s0[2]),
                        pre_state.stack_top[1],
                        pre_state.stack_top[2]),
                    self.sequence
                    )
            reduce_state1=pickle.dumps(reduce_state1)
            reduce_state2=pickle.dumps(reduce_state2)
            return [
                    (task.left_reduce,next_ind,reduce_state1,alpha_ind),
                    (task.right_reduce,next_ind,reduce_state2,alpha_ind),
                    ]
            
    def shift(self,last_ind,stat):
        state=self.State(stat,self)
        shift_inds=self.lattice.begins.get(state.span[1],[])
        rtn=[]
        for shift_ind in shift_inds:
            rtn+=state.shift(self,shift_ind)
        return rtn

    def reduce(self,last_ind,stat,pred_inds,predictors):
        rtn=[]
        st=self.State(stat,self)
        for i,predictor in enumerate(predictors) :
            pre_st=self.State(predictor,self)
            rtn+=st.reduce(self,pre_st,i)
        return rtn


    class Lattice:
        def __init__(self,l,w):
            self.weights=w
            self.items=l
            
            chars={}

            begins={}
            for i,item in enumerate(self.items) :
                begin=item[0]
                for j,c in enumerate(item[2]):
                    o=j+begin
                    if o not in chars: chars[o]=c
                if begin not in begins : begins[begin]=[]
                begins[begin].append(i)
            self.begins=begins
            self.sentence=''.join(x[1] for x in sorted(list(chars.items())))
            #print(self.sentence)
            #input()
            

    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        l,w=zip(*raw)
        self.lattice=self.Lattice(l,w)
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
        self.raw=raw
        #input()
        self.margins=[str(math.floor(math.log(float(k[1])/64.0+1))).encode() if k[1]!=None else None for k in raw]
        
        self.f_raw=[[k[2].encode(),k[3].encode()] for k,*_ in raw]


        
        l=max(x[0][1] for x in raw)
        self.stop_step=2*l-1


    def gen_features(self,span,actions):
        stat=pickle.loads(span)
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

        def _shift_f(stat,action):
            sind=action-self.shift_offset
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
            ba=chr(self.shift_offset).encode()
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
            if action>=self.shift_offset : 
                fv=_shift_f(span,action)
            else :
                fv=_reduce_f(span,action)
            fvs.append(fv[:])
        return fvs

    def moves_to_result(self,moves,raw):
        #actions=moves[1]
        actions=list(zip(*moves))[2]
        stack=[]
        arcs=[]
        for a in actions:
            if a>=self.shift_offset :
                ind=a-self.shift_offset
                key,w=raw[ind]
                #print(ind,key)
                stack.append(ind)
                ind+=1
            elif a==self.left_reduce:
                arcs.append((stack[-1],stack[-2]))
                stack.pop()
            elif a==self.right_reduce:
                arcs.append((stack[-2],stack[-1]))
                stack[-2]=stack[-1]
                stack.pop()
        while stack :
            arcs.append((stack.pop(),-1))
        arcs.sort()
        rst=set()
        #print(arcs)
        rst_result=arcs
        std_result=self.raw
        for s,d in rst_result :
            s=std_result[s][0]
            d=std_result[d][0] if d != -1 else None
            r=(s[:3],s[3],d)
            rst.add(r)
        #print(rst)
        return rst
        #input()
        return arcs

    def result_to_actions(self,result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（选择使用栈最小的）
        """
        is_leaf=collections.Counter()
        for i in range(len(result)):
            k,v=result[i]
            if 'dep' not in v : continue
            if v['dep'][1]==None : continue
            head=v['dep'][1]
            is_leaf[head]+=1
        stack=[]
        actions=[]
        for i in range(len(result)):
            k,v=result[i]
            k=tuple(k)
            if 'dep' not in v : continue
            stack.append([k,v['dep'][1],is_leaf[k]])
            actions.append(self.shift_offset+i)
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]==stack[-2][0] :
                    stack.pop()
                    stack[-1][2]-=1
                    actions.append(self.left_reduce)
                elif stack[-2][1] == stack[-1][0] :
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                    actions.append(self.right_reduce)
                else :
                    break
        return actions

    def actions_to_stats(self,raw,actions):
        stack=[[0,self.init_stat]]
        stats=[]
        for action in actions :
            stats.append(stack[-1][1])
            if action>=self.shift_offset :
                sind=action-self.shift_offset
                nexts=self.shift(stack[-1][0],stack[-1][1])
                n=[n for n in nexts if n[0]==action][0]
                stack.append([n[1],n[2]])
            else :
                nexts=self.reduce(stack[-1][0],stack[-1][1],[stack[-2][0]],[stack[-2][1]])
                n=[n for n in nexts if n[0]==action][0]
                stack.pop()
                stack.pop()
                stack.append([n[1],n[2]])

        return stats


    ## stuffs about the early update
    def set_oracle(self,raw,y) :
        self.set_raw(raw,None)
        self.std_states=[]
        std_actions=self.result_to_actions(y)#得到标准动作
        for i,stat in enumerate(self.actions_to_stats(raw,std_actions)) :
            s=pickle.loads(stat)
            self.std_states.append([s[0],s])
        
        for i,x in enumerate(self.std_states) :
            if i>0 :
                self.std_states[i].append(self.std_states[i-1][1])
        self.std_states=list(reversed(self.std_states[1:]))
        #print(self.std_states)
        std_states=list(self.actions_to_stats(raw,std_actions))
        #input()

        moves=[(pickle.loads(std_states[i])[0],std_states[i],std_actions[i])for i in range(len(std_actions))]
        self.early_stop_step=0
        return moves
    def remove_oracle(self):
        self.std_states=[]
    def early_stop(self,step,next_states,moves):
        if not moves: return False
        #print(step)
        #for next_state in next_states :
        #    st=self.State(next_state,self)
        #    print(st)

        if (not hasattr(self,"std_states")) or (not self.std_states) : return False

        if step < self.std_states[-1][0] : return False

        oracle_s=self.std_states[-1][1]
        oracle_p=self.std_states[-1][2]
        #print('oracle')
        #print(self.State(pickle.dumps(oracle_s),self))
        #print(self.State(pickle.dumps(oracle_p),self))
        if step > self.std_states[-1][0] : 
            return True
        #input()
        last_steps,last_states,actions=zip(*moves)
        for last_state,action,next_state in zip(last_states,actions,next_states):
            if last_state==b'': return False
            next_state=pickle.loads(next_state)
            if next_state == self.std_states[-1][1] : 
                #return False
                last_state=pickle.loads(last_state)
                if step==0 or last_state==self.std_states[-1][2] :
                    ps=self.std_states.pop()
                    self.early_stop_step=ps[0]
                    return False
        #print("Eearly STOP!")
        return True
    def update_moves(self,std_moves,rst_moves) :
        #print('update',self.early_stop_step)
        #for std,rst in zip(std_moves,rst_moves) :
        #    if std!= rst :
        #        yield std,1
        #        yield rst,-1
        #        return

        #return
        for std in std_moves:
            if self.early_stop_step == None or self.early_stop_step>=std[0] :
                yield std, 1
            else :
                break
        for rst in rst_moves:
            if self.early_stop_step == None or self.early_stop_step>=rst[0] :
                yield rst, -1
            else :
                break


