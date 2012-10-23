import pickle
#import marshal as pickle
import isan.parsing.dep_codec as codec
import isan.parsing.eval as eval
class Dep:
    shift_action=ord('s')
    left_reduce=ord('l')
    right_reduce=ord('r')
    #init=(0,(0,0),(None,None,None))
    def init(self):
        pass
    init_stat=pickle.dumps((0,(0,0),(None,None,None)))
    Eval=eval.Eval
    codec=codec
    def shift(self,stat):
        stat=pickle.loads(stat)
        raw=self.raw
        ind,_,stack_top=stat
        if ind>=len(raw): return []
        rtn= [
                (self.shift_action,
                    pickle.dumps(
                (ind+1,
                (ind,ind+1),
                ((raw[ind][0],raw[ind][1],None,None),
                        stack_top[0],
                        stack_top[1][1] if stack_top[1] else None)
                )))
                ]
        return rtn

    def reduce(self,stat,predictor):
        stat=pickle.loads(stat)
        ind,span,stack_top=stat
        predictor=pickle.loads(predictor)
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        assert(predictor[2][0]==s1)
        if s0==None or s1==None:return []
        rtn= [
             (self.left_reduce,pickle.dumps((ind,
                (p_span[0],span[1]),
                ((s1[0],s1[1],s1[2],s0[1]),predictor[2][1],predictor[2][2])))),
             (self.right_reduce,pickle.dumps((ind,
                (p_span[0],span[1]),
                ((s0[0],s0[1],s1[1],s0[3]),predictor[2][1],predictor[2][2])))),
             ]
        return rtn
    def set_raw(self,raw,_):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
        self.f_raw=[[w.encode()if w else b'',t.encode()if t else b''] for w,t in raw]
    def gen_features(self,stat):
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
                b'9'+s0_w+s1_w,
                b'0'+s0_t+s1_t,
                b'a'+s0_t+q0_t,
                b'b'+s0_w+s0_t+s1_t,
                b'c'+s0_t+s1_w+s1_t,
                b'd'+s0_w+s1_w+s1_t,
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
    def actions_to_result(self,actions,raw):
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
        assert(len(actions)==2*len(result)-1)

        #the following is used to check whether the rst is right
        #rst=self.actions_to_result(actions,self.raw)
        #if rst!=result :
        #    input("no !")

        return actions
    def actions_to_stats(self,actions):
        sn=sum(1 if a==self.shift_action else 0 for a in actions)
        assert(sn*2-1==len(actions))
        stat=None
        stack=[]# [ w,t,l_t,r_t , span[0],span[1]]
        ind=0
        for action in actions:
            stat=(ind,(0,0)if not stack else (stack[-1][4],stack[-1][5]),(tuple(stack[-1][:4]) if len(stack)>0 else None,
                tuple(stack[-2][:4]) if len(stack)>1 else None,
                        stack[-3][1] if len(stack)>2 else None,
                        ))
            yield pickle.dumps(stat)
            if action==self.shift_action :
                stack.append([self.raw[ind][0],self.raw[ind][1],None,None,ind,ind+1])
                ind+=1
            else :
                if action==self.left_reduce :
                    stack[-2][3]=stack[-1][1]
                    stack[-2][5]=stack[-1][5]
                    stack.pop()
                if action==self.right_reduce :
                    stack[-1][2]=stack[-2][1]
                    stack[-1][4]=stack[-2][4]
                    stack[-2]=stack[-1]
                    stack.pop()
