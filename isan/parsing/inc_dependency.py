#!/usr/bin/python3
import collections
import pickle
import sys
import random
import time
import isan.common.perceptrons as perceptrons
import isan.parsing.dep_codec as codec
"""
"""

class Defalt_Features:
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
    def __call__(self,stat):
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

class Stats :
    def __init__(self):
        self.init_stat=(0,(0,0),(None,None,None))
    def shift(self,raw,stat):
        ind,_,stack_top=stat
        if ind>=len(raw): return None
        return (ind+1,
                (ind,ind+1),
                ((raw[ind][0],raw[ind][1],None,None),
                        stack_top[0],
                        stack_top[1][1] if stack_top[1] else None)
                )
    def reduce(self,raw,stat,predictor):
        ind,span,stack_top=stat
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        if s0==None or s1==None:return None,None
        return ((ind,
                (p_span[0],span[1]),
                ((s1[0],s1[1],s1[2],s0[1]),predictor[2][1],predictor[2][2])),
             (ind,
                (p_span[0],span[1]),
                ((s0[0],s0[1],s1[1],s0[3]),predictor[2][1],predictor[2][2])),)

    def gen_stats(self,raw,actions):
        sn=sum(1 if a=='s' else 0 for a in actions)
        assert(sn*2-1==len(actions))
        stat=None
        stack=[]
        ind=0
        for action in actions:
            stat=(ind,(0,0),(stack[-1] if len(stack)>0 else None,
                        stack[-2] if len(stack)>1 else None,
                        stack[-3][1] if len(stack)>2 else None,
                        ))
            yield stat
            if action=='s':
                stack.append([raw[ind][0],raw[ind][1],None,None])
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
class Reduced_Stats :
    def __init__(self):
        self.init_stat=(0,(0,0),(None,None))
    def shift(self,raw,stat):
        ind,_,stack_top=stat
        if ind>=len(raw): return None
        return (ind+1,(ind,ind+1),(raw[ind],stack_top[0]))
    def reduce(self,raw,stat,predictor):
        ind,span,stack_top=stat
        _,p_span,_=predictor
        right,left=stack_top
        if right==None or left==None:return None,None
        return ((ind,(p_span[0],span[1]),(left,predictor[2][1])),
             (ind,(p_span[0],span[1]),(right,predictor[2][1])),)

    def gen_stats(self,raw,actions):
        sn=sum(1 if a=='s' else 0 for a in actions)
        assert(sn*2-1==len(actions))
        stat=None
        stack=[]
        ind=0
        for action in actions:
            stat=(ind,(0,0),(stack[-1] if len(stack)>0 else None,
                        stack[-2] if len(stack)>1 else None))
            yield stat
            if action=='s':
                stack.append(raw[ind])
                ind+=1
            else:
                left=stack[-2][0]
                right=stack[-1][1]
                if action=='l':
                    stack.pop()
                if action=='r':
                    stack[-2]=stack[-1]
                    stack.pop()
        
class Model :
    """
    """
    @staticmethod
    def result_to_actions(result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（没搞清楚相关工作怎么弄的）
        """
        stack=[]
        actions=[]
        record=[[ind,head,0] for ind,head in enumerate(result)]
        for ind,head,_ in record:
            if head!=-1:
                record[head][2]+=1
        for ind,head in enumerate(result):
            actions.append('s')
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                #if stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append('l')
                    stack.pop()
                    stack[-1][2]-=1
                #elif stack[-2][2]==0 and stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append('r')
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                else:
                    break
        #print(stack)
        #print(len(actions),len(result))
        #print(*enumerate(result))
        assert(len(actions)==2*len(result)-1)
        return actions

    @staticmethod
    def actions_to_result(actions):
        """
        动作序列转化为依存结果（与DP的状态设计无关）
        """
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

    def __init__(self,beam_size=16):
        self.shift_weights=perceptrons.Features()#特征
        self.lreduce_weights=perceptrons.Features()#特征
        self.rreduce_weights=perceptrons.Features()#特征
        self.features=Defalt_Features()
        self.stats=Stats()
        self.beam_size=beam_size
    
    def find_thrink(self,step):
        for stat,info in self.steps[step].items():
            info['alphas'].sort(key=lambda x:x['c'],reverse=True)
            pass
        beam=[(info,stat) for stat,info in self.steps[step].items()]
        beam.sort(reverse=True,key=lambda x:x[0]['alphas'][0]['c'])
        beam=beam[:min(len(beam),self.beam_size)]
        return [stat for _,stat in beam]

    def find_next(self,step):
        for k in self.find_thrink(step):
            fv=self.features(k)
            self._gen_next(step,k,fv)

    def _gen_next(self,step,stat,fv):
        stat_info=self.steps[step][stat]
        alphas=stat_info['alphas']
        #betas=stat_info.setdefault('betas',{})
        predictors=stat_info['pi']
        c,v=alphas[0]['c'],alphas[0]['v']
        #shift
        key=self.stats.shift(self.raw,stat)
        if key:
            if key not in self.steps[step+1]:
                self.steps[step+1][key]={'pi':set(),'alphas':[]}
            new_stat_info=self.steps[step+1][key]
            new_stat_info['pi'].add((step,stat))
            xi=self.shift_weights(fv)
            new_stat_info['alphas'].append({
                        'c':c+xi,
                        'v':0,
                        'a':'s',
                        'p':((step,stat),)})
            #betas['s']=[key]
        for p_step,predictor in predictors:
            last_stat_info=self.steps[p_step][predictor]
            last_fv=self.features(predictor)
            last_xi=self.shift_weights(last_fv)
            last_c,last_v=last_stat_info['alphas'][0]['c'],last_stat_info['alphas'][0]['v']
            lkey,rkey=self.stats.reduce(self.raw,stat,predictor)
            #left-reduce
            if lkey :
                if lkey not in self.steps[step+1]:
                    self.steps[step+1][lkey]={'pi':set(),'alphas':[]}
                new_stat_info=self.steps[step+1][lkey]
                new_stat_info['pi'].update(last_stat_info['pi'])
                lamda=self.lreduce_weights(fv)
                delta=lamda+last_xi
                new_stat_info['alphas'].append({
                            'c':last_c+v+delta,
                            'v':last_v+v+delta,
                            'a':'l',
                            'p':((step,stat),(p_step,predictor))})
                #betas['l']=[lkey]

            #right-reduce
            if rkey:
                if rkey not in self.steps[step+1]:
                    self.steps[step+1][rkey]={'pi':set(),'alphas':[]}
                new_stat_info=self.steps[step+1][rkey]
                new_stat_info['pi'].update(last_stat_info['pi'])
                rho=self.rreduce_weights(fv)
                delta=rho+last_xi
                new_stat_info['alphas'].append({
                            'c':last_c+v+delta,
                            'v':last_v+v+delta,
                            'a':'r',
                            'p':((step,stat),(p_step,predictor))})
                #betas['r']=[rkey]

    def update(self,actions,training_step,delta):
        
        #print(delta)
        #print(len(actions))
        #print(len(self.raw))
        #print(actions)
        for stat,action in zip(self.stats.gen_stats(self.raw,actions),actions):
            fv=self.features(stat)
            if action=='s': self.shift_weights.updates(fv,delta,training_step)
            if action=='l': self.lreduce_weights.updates(fv,delta,training_step)
            if action=='r': self.rreduce_weights.updates(fv,delta,training_step)

    def _find_result(self,step,stat,begin,end,actions,stats):
        if begin==end: return
        info=self.steps[step][stat]
        alpha=info['alphas'][0]
        action=alpha['a']
        actions[end-1]=alpha['a']
        if alpha['a']=='s': 
            last_ind,last_stat=alpha['p'][0]
            stats[last_ind]=last_stat
            return
        last,reduced=alpha['p']
        r_ind,r_stat=reduced
        last_ind,last_stat=last
        actions[r_ind]='s'
        stats[last_ind]=last_stat
        stats[r_ind]=r_stat
        self._find_result(r_ind,r_stat,begin,r_ind,actions,stats)
        self._find_result(last_ind,last_stat,r_ind+1,end-1,actions,stats)

            

    def decode(self,raw):
        self.raw=raw
        self.features.set_raw(raw)
        self.steps=[{} for i in range(2*len(raw))]
        self.steps[0][self.stats.init_stat]={'pi':set(),
                    'alphas':[{'c' : 0, 'v' : 0, 'a': None }]}#初始状态
        for i in range(len(raw)*2-1):
            self.find_next(i)
            
        stat=self.find_thrink(len(raw)*2-1)[0]
        step=len(raw)*2-1
        actions=[None for x in range(step)]
        stats=[None for x in range(step)]
        self._find_result(step,stat,0,step,actions,stats)
        return actions    

    def average(self,step):
        self.shift_weights.average(step)
        self.lreduce_weights.average(step)
        self.rreduce_weights.average(step)
        pass

    def save(self,filename):
        file=open(filename,'bw')
        pickle.dump(self.shift_weights,file)
        pickle.dump(self.lreduce_weights,file)
        pickle.dump(self.rreduce_weights,file)
        file.close()
    def load(self,filename):
        file=open(filename,'rb')
        self.shift_weights=pickle.load(file)
        self.lreduce_weights=pickle.load(file)
        self.rreduce_weights=pickle.load(file)
        file.close()
        

def train(model,training,iteration=10):
    stats=model
    step=0
    for i in range(iteration):
        std,cor=0,0
        otime=time.time()
        for ln,line in enumerate(open(training)):
            step+=1
            #if ln>100:break
            line=line.strip()
            sen=codec.decode(line)
            raw=[(word,tag) for word,tag,_,_ in sen]
            if not raw:
                print('x',line)
            std_result=[x for _,_,x,_ in sen]
            #print(raw)
            rst_actions=stats.decode(raw)
            rst_result=stats.actions_to_result(rst_actions)
            std_actions=stats.result_to_actions(std_result)
            #print(std_result)
            #print(rst_result)
            #print(std_actions)
            #print(rst_actions)
            #input()
            #print(ln)
            std+=len(std_result)
            cor+=sum(1 if s==r else 0 for s,r in zip(std_result,rst_result))
            if std_result!=rst_result:
                stats.update(rst_actions,step,-1)
                stats.update(std_actions,step,1)
        print(i+1,cor/std,time.time()-otime)
    model.average(step)

def test(model,test):
    stats=model
    std,cor=0,0
    for ln,line in enumerate(open(test)):
        line=line.strip()
        sen=codec.decode(line)
        raw=[(word,tag) for word,tag,_,_ in sen]
        std_result=[x for _,_,x,_ in sen]
        #print(raw)
        rst_actions=stats.decode(raw)
        rst_result=stats.actions_to_result(rst_actions)
        std_actions=stats.result_to_actions(std_result)
        std+=len(std_result)
        '''for i in range(len(raw)):
            if raw[i][1]!='PU':
                std+=1
                if std_result[i]==rst_result[i]:cor+=1'''
        cor+=sum(1 if s==r else 0 for s,r in zip(std_result,rst_result))
        #print(cor/std)
        '''print(raw)
        for ind,s,r in zip(range(len(sen)),std_result,rst_result):
            if s!=r:
                print(raw[ind],raw[s],raw[r])'''
    print(cor/std)
def predict(model,cor=sys.stdin,output=sys.stdout):
    stats=model
    for line in cor:
        line=line.strip()
        raw=[item.split('_')[:2] for item in line.split()]
        #print(raw)
        rst_actions=stats.decode(raw)
        rst_result=stats.actions_to_result(rst_actions)
        print(codec.encode(raw,rst_result),file=output)

if __name__=="__main__":
    pass
