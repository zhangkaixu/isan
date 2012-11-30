import pickle
import json
import collections
import math

#import marshal as pickle
import isan.parsing.ldep_eval as eval
class Dep:
    name="依存句法分析"

    def __init__(self):
        self.Y=None
    
    shift_action=ord('s')
    left_reduce=ord('l')
    right_reduce=ord('r')

    def check(self,std_moves,rst_moves):
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
            #lat=[x for x in lat if 'dep' in x[1]]
            #print(lat)
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
            return {'raw':raw,'y':lat}

    def shift(self,last_ind,stat):
        stat=pickle.loads(stat)
        ind,span,stack_top,sequence=stat
        if span[1] not in (self.begins) : return []
        shift_inds=self.begins[span[1]]
        if len(shift_inds)==0 : return []
        raw=self.raw
        rtn=[]
        for shift_ind in shift_inds :
            shift_key,weight=raw[shift_ind]
            next_ind=last_ind+2*len(shift_key[2])-1
            if next_ind==self.stop_step : next_ind = -1
            state=(
                    (next_ind,
                    (shift_key[0],shift_key[1]),
                    ((shift_ind,None,None),
                            stack_top[0],
                            self.spans[stack_top[1][0]][3] if stack_top[1] else None),
                    (shift_ind,sequence[0]),
                    )
                    )
            #print(state,next_ind)
            data=(1000+shift_ind,
                    next_ind,
                        pickle.dumps(state),
                    )
            rtn.append(data)
        #input()
        #print('end of shift',len(rtn))
        return rtn

    def reduce(self,last_ind,stat,pred_inds,predictors):
        #print('in reduce',last_ind)
        rtn=[]
        i=0
        for ind,predictor in zip(pred_inds, predictors) :
            s=self.reduce_one(last_ind,stat,ind,predictor,i)
            rtn+=s
            i+=1

        #print(len(rtn))
        #input()
        #print('end of reduce')
        return rtn

    def reduce_one(self,last_ind,stat,pred_inds,predictor,alpha_ind):
        stat=pickle.loads(stat)
        next_ind=last_ind+1 if last_ind+1 < self.stop_step else -1
        #print(next_ind)
        #if next_ind==-1:
        #    print('-1')

        ind,span,stack_top,sequence=stat
        predictor=pickle.loads(predictor)
        _,p_span,_,_=predictor
        s0,s1,s2=stack_top
        assert(predictor[2][0]==s1)
        if s0==None or s1==None:return []
        rtn= [
             (self.left_reduce,next_ind,pickle.dumps((next_ind,
                (p_span[0],span[1]),
                ((s1[0],s1[1],self.spans[s0[0]][3]),predictor[2][1],predictor[2][2]),
                sequence
                )),
                alpha_ind),
             (self.right_reduce,next_ind,pickle.dumps((next_ind,
                (p_span[0],span[1]),
                ((s0[0],self.spans[s1[0]][3],s0[2]),predictor[2][1],predictor[2][2]),
                sequence
                )),
                alpha_ind),
             ]
        return rtn
    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
        self.spans=[k[0] for k in raw]
        self.margins=[str(math.floor(math.log(float(k[1])/64.0+1))).encode() if k[1]!=None else None for k in raw]
        
        self.f_raw=[[k[2].encode(),k[3].encode()] for k,*_ in raw]
        begins={}
        ind=0
        for k,*_ in raw :
            if k[0] not in begins : begins[k[0]]=[]
            begins[k[0]].append(ind)
            ind+=1
        self.begins=begins

        
        l=max(x[0][1] for x in raw)
        self.stop_step=2*l-1


    def gen_features(self,span,actions):
        def gen_features_one(stat,action=0):
            q0_w,q0_t=(b'#',b'#')
            if action>1000 :
                sind=action-1000
                q0_w,q0_t=self.f_raw[sind]

            stat=pickle.loads(stat)
            ind,_,stack_top,sequence=stat
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
            
            fv=[
                    b'len'+str(len(s0_w)).encode(),
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
                    b'h'+s0_t+s1_t+q0_t,
                    b'j'+s0_w+s1_t+q0_t,
                    #(4)
                    b'k'+s0_t+s1_t+s1l_t,
                    b'l'+s0_t+s1_t+s1r_t,
                    b'm'+s0_t+s1_t+s0l_t,
                    b'n'+s0_t+s1_t+s0r_t,
                    b'o'+s0_w+s1_t+s0l_t,
                    b'p'+s0_w+s1_t+s0r_t,
                    ]
            if s0_m :
                fv+=[b'M'+s0_m]
            return fv
        fvs=[]
        for action in actions:
            fv=gen_features_one(span,action)
            if action> 1000 :
                action=1000
            action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

    def moves_to_result(self,moves,raw):
        #actions=moves[1]
        actions=list(zip(*moves))[2]
        #print(actions)
        stack=[]
        arcs=[]
        for a in actions:
            if a>=1000:
                ind=a-1000
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
        arcs.append((stack[-1],-1))
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
            actions.append(1000+i)
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
            #print(pickle.loads(stats[-1]))
            if action>=1000 :
                sind=action-1000
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
        self.early_stop_step=None
        return moves
    def remove_oracle(self):
        self.std_states=[]
    def early_stop(self,step,next_states,moves):
        if not moves: return False
        last_steps,last_states,actions=zip(*moves)
        if (not hasattr(self,"std_states")) or (not self.std_states) : return False

        if step < self.std_states[-1][0] : return False
        if step > self.std_states[-1][0] : 
            self.early_stop_step=step
            return True
        for last_state,action,next_state in zip(last_states,actions,next_states):
            if last_state==b'': return False
            next_state=pickle.loads(next_state)
            if next_state == self.std_states[-1][1] : 
                last_state=pickle.loads(last_state)
                if step==0 or last_state==self.std_states[-1][2] :
                    self.std_states.pop()
                    return False
        self.early_stop_step=step
        return True
    def update_moves(self,std_moves,rst_moves) :
        #print(self.early_stop_step)
        for std,rst in zip(std_moves,rst_moves):
            if self.early_stop_step == None or self.early_stop_step>std[0] :
                yield std, 1
            else :
                #print(std[0])
                pass
            if self.early_stop_step == None or self.early_stop_step>rst[0] :
                yield rst, -1
            else :
                #print(rst[0])
                pass

        #input()

