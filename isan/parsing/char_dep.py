import pickle
import json
import time
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
    class Eval:
        def __init__(self):
            self.start_time=time.time()
        def __call__(self,a,b,**_):
            raw=''.join(a)

            mer=[i for i in range(len(raw))]
            for i,r in enumerate(b):
                if r!=-1 :
                    if abs(i-r)==1 :
                        mer[i]=r

            lx=-1
            sen=[]
            for x,c in zip(mer,raw):
                if x!=lx:
                    sen.append('')
                    lx=x
                sen[-1]+=c
            print(' '.join(sen))


            pass
        def print_result(self):
            duration=time.time()-self.start_time
            print("历时:%.2f 现时:%s"%(
                    duration,
                    time.strftime("%H:%M:%S")))
            pass
        pass
    class codec:
        def decode(line):
            data=json.loads(line.strip())
            return data
    def shift(self,stat):
        stat=pickle.loads(stat)
        raw=self.raw
        ind,span,stack_top=stat
        l,r=span
        if self.intervals:
            if self.intervals[l][1]!=-1 and self.intervals[l][1]<=r: return []

        if ind>=len(raw): return []
        rtn= [
                (self.shift_action,
                    pickle.dumps(
                (ind+1,
                (ind,ind+1),
                (raw[ind][0],
                        stack_top[0],
                        stack_top[1])
                )))
                ]
        return rtn

    def reduce(self,stat,predictor):
        stat=pickle.loads(stat)
        ind,span,stack_top=stat
        predictor=pickle.loads(predictor)
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        if s0==None or s1==None:return []
        l,r=p_span[0],span[1]
        if self.intervals:
            if self.intervals[l][1]!=-1 and self.intervals[l][1]<r: return []
            if self.intervals[r][0]!=-1 and self.intervals[r][1]>l: return []
        s01=s1+s0
        rtn= [
            (self.left_reduce,pickle.dumps((ind,
                (p_span[0],span[1]),
                (s01 if len(s01)<=2 else s1,predictor[2][1],predictor[2][2])))),
             (self.right_reduce,pickle.dumps((ind,
                (p_span[0],span[1]),
                (s01 if len(s01)<=2 else s0,predictor[2][1],predictor[2][2])))),
             ]
        return rtn
    def actions_to_stats(self,actions):
        sn=sum(1 if a==self.shift_action else 0 for a in actions)
        assert(sn*2-1==len(actions))
        stat=None
        stack=[]
        ind=0
        for action in actions:
            stat=(ind,(0,0)if not stack else (stack[-1][4],stack[-1][5]),
                    (
                        stack[-1][0] if len(stack)>0 else None,
                        stack[-2][0] if len(stack)>1 else None,
                        stack[-3][0] if len(stack)>2 else None,
                    ))
            yield pickle.dumps(stat)
            if action==self.shift_action:
                stack.append([self.raw[ind],self.raw[ind],None,None,ind,ind+1])
                ind+=1
            else:
                s01=stack[-1][0]+stack[-2][0]
                if action==self.left_reduce:
                    if len(s01)<=2 :
                        stack[-2][0]=s01
                    stack[-2][3]=stack[-1][1]
                    stack[-2][5]=stack[-1][5]
                    stack.pop()
                if action==self.right_reduce:
                    stack[-1][2]=stack[-2][1]
                    stack[-1][4]=stack[-2][4]
                    stack[-2]=stack[-1]
                    if len(s01)<=2 :
                        stack[-2][0]=s01
                    stack.pop()
    def set_raw(self,raw,Y):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        if Y:
            self.intervals=Y[1]
        else:
            self.intervals=None
        self.raw=raw
        self.f_raw=[w.encode() for w in self.raw]
    def gen_features(self,stat):
        stat=pickle.loads(stat)
        ind,_,stack_top=stat
        s0,s1,s2=stack_top

        q0=self.f_raw[ind] if ind<len(self.f_raw) else b''
        q1=self.f_raw[ind+1] if ind+1<len(self.f_raw) else b''
        c0=self.f_raw[ind-1] if ind-1>=0 else b''

        s0=(s0.encode() if s0 else b'')
        s1=(s1.encode() if s1 else b'')
        s2=(s2.encode() if s2 else b'')

        
        
        fv=[
                b'0'+s0,
                b'1'+s1,
                b'2'+s2,
                b'3'+s1+b' '+s2,
                b'4'+s0+b' '+q0,
                b'5'+q0+b' '+q1,
                b'6'+q0,
                b'6'+c0,
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
        record=[[ind,head,0] for ind,head in enumerate(result)]
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
        return actions
