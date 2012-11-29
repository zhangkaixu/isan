import pickle
import json
import collections

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
    init_stat=pickle.dumps((0,(0,0),(None,None,None)))
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
                raw.append([k,v.get('tag-weight',None)])
                if 'dep' in v and v['dep'][1]!=None :
                    v['dep'][1]=tuple(v['dep'][1])
            return {'raw':raw,'y':lat}

    def shift(self,last_ind,stat):
        stat=pickle.loads(stat)
        #print('in shift',last_ind)
        #print(stat)
        ind,span,stack_top=stat
        #print(ind,span)
        #print(self.begins)
        if span[1] not in (self.begins) : return []
        shift_inds=self.begins[span[1]]
        #print(shift_inds)
        if len(shift_inds)==0 : return []
        raw=self.raw
        rtn=[]
        for shift_ind in shift_inds :
            shift_key,weight=raw[shift_ind]
            next_ind=last_ind+2*len(shift_key[2])-1
            state=(
                    (next_ind,
                    (shift_key[0],shift_key[1]),
                    ((shift_key[2],shift_key[3],None,None),
                            stack_top[0],
                            stack_top[1][1] if stack_top[1] else None)
                    ))
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

        ind,span,stack_top=stat
        predictor=pickle.loads(predictor)
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        assert(predictor[2][0]==s1)
        if s0==None or s1==None:return []
        rtn= [
             (self.left_reduce,next_ind,pickle.dumps((next_ind,
                (p_span[0],span[1]),
                ((s1[0],s1[1],s1[2],s0[1]),predictor[2][1],predictor[2][2]))),
                alpha_ind),
             (self.right_reduce,next_ind,pickle.dumps((next_ind,
                (p_span[0],span[1]),
                ((s0[0],s0[1],s1[1],s0[3]),predictor[2][1],predictor[2][2]))),
                alpha_ind),
             ]
        return rtn
    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
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
        fvs=[]
        fv=self.gen_features_one(span)
        for action in actions:
            if action> 1000 :
                action=1000
            action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

    def gen_features_one(self,stat):
        stat=pickle.loads(stat)
        ind,_,stack_top=stat
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

        
        fv=[
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
                ]
        #print(*[x.decode() for x in fv])
        #input()
        return fv
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
        #sn=sum(1 if a==self.shift_action else 0 for a in actions)
        #assert(sn*2-1==len(actions))
        stat=None
        stack=[]# [ w,t,l_t,r_t , span[0],span[1]]
        step=0
        for action in actions:
            stat=(step,(0,0)if not stack else (stack[-1][4],stack[-1][5]),(tuple(stack[-1][:4]) if len(stack)>0 else None,
                tuple(stack[-2][:4]) if len(stack)>1 else None,
                        stack[-3][1] if len(stack)>2 else None,
                        ))
            yield pickle.dumps(stat)
            if action>=1000 :
                sind=action-1000
                k=raw[sind][0]
                stack.append([k[2],k[3],None,None,k[0],k[1]])
                step+=2*len(k[2])-1
            else :
                step+=1
                if action==self.left_reduce :
                    stack[-2][3]=stack[-1][1]
                    stack[-2][5]=stack[-1][5]
                    stack.pop()
                if action==self.right_reduce :
                    stack[-1][2]=stack[-2][1]
                    stack[-1][4]=stack[-2][4]
                    stack[-2]=stack[-1]
                    stack.pop()

    ## stuffs about the early update
    def set_oracle(self,raw,y) :
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
        moves=[(i,std_states[i],std_actions[i])for i in range(len(std_actions))]
        return moves
    def remove_oracle(self):
        self.std_states=[]
    def early_stop(self,step,next_states,moves):
        #print('eee',step)
        #print(len(moves),len(next_states))
        if not moves: return False
        last_steps,last_states,actions=zip(*moves)
        



        if (not hasattr(self,"std_states")) or (not self.std_states) : return False
        #print(self.std_states[-1])
        #input()

        if step < self.std_states[-1][0] : return False
        if step > self.std_states[-1][0] : 
            #print('early')
            return True
        for last_state,action,next_state in zip(last_states,actions,next_states):
            if last_state==b'': return False
            next_state=pickle.loads(next_state)
            #print(next_state)
            #print(self.std_states[-1])
            if next_state == self.std_states[-1][1] : 
                last_state=pickle.loads(last_state)
                if step==0 or last_state==self.std_states[-1][2] :
                    self.std_states.pop()
                    #print('hehe')
                    return False
        #print('early')
        return True
    def update_moves(self,std_moves,rst_moves) :
        for std,rst in zip(std_moves,rst_moves):
            yield std, 1
            yield rst, -1

