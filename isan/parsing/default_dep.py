import pickle
#import marshal as pickle
import isan.parsing.dep_codec as codec
import isan.parsing.eval as eval
class Dep:
    name="依存句法分析"

    def __init__(self):
        self.ae={}
        #for line in open("large.50.99.txt"):
        #for line in open("/home/zkx/wordtype/autoencoder/30words.9.txt"):
        #for line in open("/home/zkx/wordtype/autoencoder/70words.9.txt"):
        #    word,*inds=line.split()
        #    inds=[x.encode() for x in inds]
        #    self.ae[word]=inds

        self.Y=None
    
    shift_action=ord('s')
    left_reduce=ord('l')
    right_reduce=ord('r')
    #init=(0,(0,0),(None,None,None))

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
    codec=codec
    def shift(self,last_ind,stat):
        # 计算下一步的序号
        next_ind=last_ind+1 if last_ind+1 <= (2*len(self.raw)-2) else -1
        # 当前状态
        stat=pickle.loads(stat)
        raw=self.raw
        ind,span,stack_top=stat
        if ind>=len(raw): return [] # 到头了，不能shift了
        rtn= [
                (self.shift_action,next_ind,
                    pickle.dumps(
                (ind+1, # 步数
                (ind,ind+1), # stack top 的 span
                ((ind,None,None),
                        stack_top[0],
                        stack_top[1][0] if stack_top[1] else None)
                )))
                ]
        return rtn

    def reduce(self,last_ind,stat,pred_inds,predictors):
        rtn=[]
        i=0
        for ind,predictor in zip(pred_inds, predictors) :
            s=self.reduce_one(last_ind,stat,ind,predictor,i)
            rtn+=s
            i+=1
        return rtn

    def reduce_one(self,last_ind,stat,pred_inds,predictor,alpha_ind):
        stat=pickle.loads(stat)
        next_ind=last_ind+1 if last_ind+1 <= (2*len(self.raw)-2) else -1

        ind,span,stack_top=stat
        predictor=pickle.loads(predictor)
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        assert(predictor[2][0]==s1)
        if s0==None or s1==None:return []
        rtn= [
             (self.left_reduce,next_ind,pickle.dumps((ind, # ind
                (p_span[0],span[1]), #span
                ((s1[0],s1[1],s0[0]),predictor[2][1],predictor[2][2]))), ##
                alpha_ind),
             (self.right_reduce,next_ind,pickle.dumps((ind, #
                (p_span[0],span[1]),
                ((s0[0],s1[0],s0[2]),predictor[2][1],predictor[2][2]))),
                alpha_ind),
             ]
        return rtn

    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
        #self.dbg= (raw[0][0]=='当然')
        self.reduce_rules=None
        self.shift_rules=None
        self.f_raw=[[w.encode()if w else b'',t.encode()if t else b''] for w,t in raw]

        #self.ae_inds=[]
        #for word,tag in raw :
        #    if len(word)==1 :
        #        self.ae_inds.append([])
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
        ind,_,stack_top=stat
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
            aeind0h=[]

        if s1:
            s1m,s1l,s1r=s1
            s1l_t=b'~' if s1l is None else self.f_raw[s1l][1]
            s1r_t=b'~' if s1r is None else self.f_raw[s1r][1]
            s1_w=self.f_raw[s1m][0]
            s1_t=self.f_raw[s1m][1]
        else:
            s1_w,s1_t,s1l_t,s1r_t=b'~',b'~',b'~',b'~'

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

        #for aeind in aeind0h :
        #    fv+=[
        #            b'q0_taeind0~'+q0_t+aeind,
        #            b's0lt_taeind0~'+s0l_t+aeind,
        #            b's0rt_taeind0~'+s0r_t+aeind,
        #            b's1t_taeind0~'+s1_t+aeind,
        #            ]

        return fv
    def moves_to_result(self,moves,raw):
        #actions=moves[1]
        actions=list(zip(*moves))[2]
        ind=0
        stack=[]
        arcs=[]
        for a in actions:
            if a==self.shift_action:
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
        arcs=[x for _,x in arcs]
        return arcs

        sen=[]
        cache=''
        for c,a in zip(raw,actions[1:]):
            cache+=c
            if a==self.shift_action:
                sen.append(cache)
                cache=''
        if cache:
            sen.append(cache)
        return sen
    def result_to_actions(self,result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（没搞清楚相关工作怎么弄的）
        """
        stack=[]
        actions=[]
        result=[ind for _,_,ind,_ in result]
        record=[[ind,head,0] for ind,head in enumerate(result)]# [ind, ind_of_head, 是head的次数]
        for ind,head,_ in record:
            if head!=-1 :
                record[head][2]+=1
        for ind,head in enumerate(result):
            actions.append(self.shift_action)
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append(self.left_reduce)
                    stack.pop()
                    stack[-1][2]-=1
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append(self.right_reduce)
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                else:
                    break

        #assert(len(actions)==2*len(result)-1)

        #the following is used to check whether the rst is right
        #rst=self.actions_to_result(actions,self.raw)
        #if rst!=result :
        #    input("no !")

        return actions
    def actions_to_stats(self,raw,actions):
        sn=sum(1 if a==self.shift_action else 0 for a in actions)
        #assert(sn*2-1==len(actions))
        stat=None
        #stack=[]# [ w,t,l_t,r_t , span[0],span[1]]
        stack=[]# [ w_ind,l_ind,r_ind , span[0],span[1]]
        ind=0
        for action in actions:
            stat=(ind,(0,0)if not stack else (stack[-1][3],stack[-1][4]),
                    (
                        tuple(stack[-1][:3]) if len(stack)>0 else None,
                        tuple(stack[-2][:3]) if len(stack)>1 else None,
                        stack[-3][0] if len(stack)>2 else None,
                        ))
            yield pickle.dumps(stat)
            if action==self.shift_action :
                stack.append([ind,None,None,ind,ind+1])
                ind+=1
            else :
                if action==self.left_reduce :
                    stack[-2][2]=stack[-1][0]
                    stack[-2][4]=stack[-1][4]
                    stack.pop()
                if action==self.right_reduce :
                    stack[-1][1]=stack[-2][0]
                    stack[-1][3]=stack[-2][3]
                    stack[-2]=stack[-1]
                    stack.pop()

    ## stuffs about the early update
    def set_oracle(self,raw,y) :
        self.std_states=[]
        std_actions=self.result_to_actions(y)#得到标准动作
        for i,stat in enumerate(self.actions_to_stats(raw,std_actions)) :
            self.std_states.append(stat)
        std_states=list(self.actions_to_stats(raw,std_actions))
        moves=[(i,std_states[i],std_actions[i])for i in range(len(std_actions))]
        return moves
    def early_stop(self,step,next_states,moves):
        last_steps,last_states,actions=zip(*moves)
        if (not hasattr(self,"std_states")) or (not self.std_states) : return False
        for last_state,action,next_state in zip(last_states,actions,next_states):
            if last_state==b'': return False
            next_state=pickle.loads(next_state)
            std_state=pickle.loads(self.std_states[step])
            #print(next_state,std_state)
            #input()
            if next_state == std_state : 
                last_state=pickle.loads(last_state)
                if step==0 or last_state==pickle.loads(self.std_states[step-1]) :
                    return False
        #print('early')
        return True
    def remove_oracle(self):
        self.std_states=[]
    def update_moves(self,std_moves,rst_moves) :
        for std,rst in zip(std_moves,rst_moves):
            yield std, 1
            yield rst, -1

