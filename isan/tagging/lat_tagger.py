import pickle
import json
import collections
import math

#import marshal as pickle
import isan.tagging.lat_eval as eval
class Dep:
    name="分词词性标注"

    def __init__(self):
        self.Y=None
    
    #shift_action=ord('s')
    #left_reduce=ord('l')
    #right_reduce=ord('r')

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
            raw=[]
            for i in range(len(lat)):
                k,v =lat[i]
                k=tuple(k)
                lat[i][0]=k
                if not ('is_test' in v and v['is_test']) :
                #if True:
                #if ('tag-weight' in v and v['tag-weight']==0) :
                    raw.append([k,v.get('tag-weight',None)])
                
                if 'dep' in v and v['dep'][1]!=None :
                    v['dep'][1]=tuple(v['dep'][1])
            return {'raw':raw,'y':lat}

    reduce=None
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
            next_ind=last_ind+len(shift_key[2])
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
            data=(shift_ind,
                    next_ind,
                        pickle.dumps(state),
                    )
            rtn.append(data)
        #print('end of shift',len(rtn))
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
        self.stop_step=l


    def gen_features(self,span,actions):
        stat=pickle.loads(span)
        ind,_,stack_top,sequence=stat
        w0_w,w0_t=b'~',b'~'
        w1_w,w1_t=b'~',b'~'
        if sequence[0]!=None :
            w0_w,w0_t=self.f_raw[sequence[0]]
        if sequence[1]!=None :
            w1_w,w1_t=self.f_raw[sequence[1]]

        
        fvs=[]

        for action in actions:
            q0_w,q0_t=self.f_raw[action]
            q0_m=b'~'
            if self.margins[action] is not None :
                q0_m=self.margins[action]
            fv=[
                    b'q0m'+q0_m,
                    b'S7'+w0_w+b'~'+q0_w,
                    b'S8'+w0_w+b'~'+q0_t,
                    b'S9'+w0_t+b'~'+q0_w,
                    b'Sa'+w0_t+b'~'+q0_t,
                    b'Sb'+w1_t+b'~'+w0_t+b'~'+q0_t,
                    ]

            fvs.append(fv)
        return fvs

    def moves_to_result(self,moves,raw):
        actions=list(zip(*moves))[2]
        rst=[self.spans[a] for a in actions]

        rst={((b,e,w,),t,None)for b,e,w,t in rst}
        return rst

    def result_to_actions(self,result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（选择使用栈最小的）
        """
        actions=[]
        for i in range(len(result)):
            k,v=result[i]
            k=tuple(k)
            if 'dep' not in v : continue
            actions.append(i)
        return actions

    def actions_to_stats(self,raw,actions):
        stack=[[0,self.init_stat]]
        stats=[]
        for action in actions :
            stats.append(stack[-1][1])
            sind=action
            nexts=self.shift(stack[-1][0],stack[-1][1])
            n=[n for n in nexts if n[0]==action][0]
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
        if (not hasattr(self,"std_states")) or (not self.std_states) : return False

        if step < self.std_states[-1][0] : return False
        if step > self.std_states[-1][0] : 
            return True
        last_steps,last_states,actions=zip(*moves)

        for last_state,action,next_state in zip(last_states,actions,next_states):
            if last_state==b'': return False
            next_state=pickle.loads(next_state)
            if next_state == self.std_states[-1][1] : 
                last_state=pickle.loads(last_state)
                if step==0 or last_state==self.std_states[-1][2] :
                    ps=self.std_states.pop()
                    self.early_stop_step=ps[0]
                    return False
        #for last_state,action,next_state in zip(last_states,actions,next_states):
        #    next_state=pickle.loads(next_state)
        #    last_state=pickle.loads(last_state)
        #    print(next_state,last_state)
        #    print(self.std_states[-1][1:])
        #    print()

        #print('final early')
        return True
    def update_moves(self,std_moves,rst_moves) :
        #print('update',self.early_stop_step)
        for std in std_moves:
            if self.early_stop_step>=std[0] :
                yield std, 1
            else :
                break
                #print(std[0])
        for rst in rst_moves:
            if self.early_stop_step>=rst[0] :
                yield rst, -1
            else :
                break
                #print(rst[0])


