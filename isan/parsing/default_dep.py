import isan.parsing.dep_codec as codec
import isan.parsing.eval as eval
class Dep:
    init=(0,(0,0),(None,None,None))
    Eval=eval.Eval
    codec=codec
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
    def gen_features(self,stat):
        ind,_,stack_top=stat
        s0,s1,s2_t=stack_top
        s0_w,s0_t,s0l_t,s0r_t=None,None,None,None
        if s0:
            s0_w,s0_t,s0l_t,s0r_t=s0
        s1_w,s1_t,s1l_t,s1r_t=None,None,None,None
        if s1:
            s1_w,s1_t,s1l_t,s1r_t=s1
        q0_w,q0_t=self.raw[ind] if ind<len(self.raw) else (None,None)
        q1_w,q1_t=self.raw[ind+1] if ind+1<len(self.raw) else (None,None)
        
        fv=[('s1w',s0_w),('s1t',s0_t),('s1ws1t',s0_w,s0_t),
            ('s2w',s1_w),('s2t',s1_t),('s2ws2t',s1_w,s1_t),
            ('q0w',q0_w),('q0t',q0_t),('q0wq0t',q0_w,q0_t),
            ('s1ws2w',s0_w,s1_w),('s1ts2t',s0_t,s1_t),
            ('s1tq0t',s0_t,q0_t),('s1ws1ts2t',s0_w,s0_t,s1_t),
            ('s1ts2ws2t',s0_t,s1_w,s1_t),('s1ws1ts2w',s0_w,s0_t,s1_w),
            ('s1ws2ws2t',s0_w,s1_w,s1_t),('s1ws1ts2ws2t',s0_w,s0_t,s1_w,s1_t),
            ('s1tq0tq1t',s0_t,q0_t,q1_t),('s1ts2tq0t',s0_t,s1_t,q0_t),
            ('s1wq0tq1t',s0_w,q0_t,q1_t),('s1ws2tq0t',s0_w,s1_t,q0_t),
            ('s0ts1ts0lt',s0_t,s1_t,s0l_t),('s0ts1ts0rt',s0_t,s1_t,s0r_t),
            ('s0ts1ts1lt',s0_t,s1_t,s1l_t),('s0ts1ts1rt',s0_t,s1_t,s1r_t),
            ('s0ts0ws0lt',s0_t,s0_w,s0l_t),('s0ts0ws0rt',s0_t,s0_w,s0r_t),
            ('s0ts1ts2t',s0_t,s1_t,s2_t),
                ]
        return fv
    @staticmethod
    def actions_to_result(actions,raw):
        ind=0
        stack=[]
        arcs=[]
        for a in actions:
            if a=='s':
                stack.append(ind)
                ind+=1
            elif a=='l':
                arcs.append((stack[-1],stack[-2]))
                stack.pop()
            elif a=='r':
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
            if a=='s':
                sen.append(cache)
                cache=''
        if cache:
            sen.append(cache)
        return sen
    @staticmethod
    def result_to_actions(result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（没搞清楚相关工作怎么弄的）
        """
        stack=[]
        actions=[]
        result=[ind for _,_,ind,_ in result]
        record=[[ind,head,0] for ind,head in enumerate(result)]
        for ind,head,_ in record:
            if head!=-1 :
                record[head][2]+=1
        for ind,head in enumerate(result):
            actions.append('s')
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append('l')
                    stack.pop()
                    stack[-1][2]-=1
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append('r')
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                else:
                    break
        assert(len(actions)==2*len(result)-1)
        return actions
    def actions_to_stats(self,actions):
        sn=sum(1 if a=='s' else 0 for a in actions)
        assert(sn*2-1==len(actions))
        stat=None
        stack=[]
        ind=0
        for action in actions:
            stat=(ind,(0,0),(tuple(stack[-1]) if len(stack)>0 else None,
                        tuple(stack[-2]) if len(stack)>1 else None,
                        tuple(stack[-3][1]) if len(stack)>2 else None,
                        ))
            yield stat
            if action=='s':
                stack.append([self.raw[ind][0],self.raw[ind][1],None,None])
                ind+=1
            else:
                left=stack[-2][0]
                right=stack[-1][1]
                if action=='l':
                    stack[-2][3]=stack[-1][1]
                    stack.pop()
                if action=='r':
                    stack[-1][2]=stack[-2][1]
                    stack[-2]=stack[-1]
                    stack.pop()
    def shift(self,stat):
        raw=self.raw
        ind,_,stack_top=stat
        if ind>=len(raw): return []
        return [
                ('s',
                (ind+1,
                (ind,ind+1),
                ((raw[ind][0],raw[ind][1],None,None),
                        stack_top[0],
                        stack_top[1][1] if stack_top[1] else None)
                ))
                ]
    def reduce(self,stat,predictor):
        raw=self.raw
        ind,span,stack_top=stat
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        if s0==None or s1==None:return []
        return [
            ('l',(ind,
                (p_span[0],span[1]),
                ((s1[0],s1[1],s1[2],s0[1]),predictor[2][1],predictor[2][2]))),
             ('r',(ind,
                (p_span[0],span[1]),
                ((s0[0],s0[1],s1[1],s0[3]),predictor[2][1],predictor[2][2]))),
             
             ]
