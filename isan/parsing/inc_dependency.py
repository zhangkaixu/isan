#!/usr/bin/python3
import collections
import pickle
import sys
import random
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
        pass
    def __call__(self,stat):
        ind,stack_top=stat
        top1,top2=stack_top
        
        fv=[('s1',top1[2] if top1 else None),
                ('s2',top2[2] if top2 else None)]
        return fv
        
    #def update(self,stat,delta,step=0):
    #    """
    #    更新权重
    #    """
    #    self.features.updates(self._key_gen(stat),delta,step)
        
class Shift_Reduce_Stat:
    """
    步数 :
    (解析位置, (栈顶若干元素)) :
    [set(predictors),alphas,betas]
        alpha=(score,step_score,action,last_stat)
    """
    def __init__(self):
        self.shift_weights=perceptrons.Features()#特征
        self.lreduce_weights=perceptrons.Features()#特征
        self.rreduce_weights=perceptrons.Features()#特征
        self.features=Defalt_Features()

    def cal_score(self,step):
        for stat,info in self.steps[step].items():
            predictors,alphas,betas=info
            for alpha in alphas:
                alpha[0]=0
                alpha[1]=2
                #print(stat,alpha[:])
                pass
    def find_thrink(self,step):
        self.cal_score(step)
        for stat,info in self.steps[step].items():
            predictors,alphas,betas=info
            alphas.sort(reverse=True)
        beam=[(info,stat) for stat,info in self.steps[step].items()]
        beam.sort(reverse=True)
        beam=beam[:min(len(beam),5)]
        return [stat for _,stat in beam]

    def find_next(self,step):
        for k in self.find_thrink(step):
            fv=self.features(k)
            self._gen_next(step,k,fv)


    
    def _gen_next(self,step,stat,fv):
        ind,stack_top=stat
        predictors,alphas,betas=self.steps[step][stat]
        alpha_value=alphas[0][0]
        #shift
        if ind<len(self.raw):
            key=(ind+1,((ind,ind+1,self.raw[ind]),stack_top[0]))
            if key not in self.steps[step+1]:
                self.steps[step+1][key]=[set(),[],[]]
            new_stat_info=self.steps[step+1][key]
            new_stat_info[0].add((step,stat))
            delta=self.shift_weights(fv)
            new_stat_info[1].append([alpha_value+delta,delta,'s',stat])
            betas.append([None,delta,'s',key])
        if stack_top[0]!=None and stack_top[1]!=None:
            right,left=stack_top

            for p_step,predictor in predictors:
                last_stat_info=self.steps[p_step][predictor]
                #left-reduce
                key=(ind,((left[0],right[1],left[2] ),predictor[1][1]))
                if key not in self.steps[step+1]:
                    self.steps[step+1][key]=[set(),[],[]]
                new_stat_info=self.steps[step+1][key]
                new_stat_info[0].update(last_stat_info[0])
                delta=self.lreduce_weights(fv)
                new_stat_info[1].append([alpha_value+delta,delta,'l',stat])
                betas.append([None,delta,'l',key])

                #right-reduce
                key=(ind,((left[0],right[1],right[2]),predictor[1][1]))
                if key not in self.steps[step+1]:
                    self.steps[step+1][key]=[set(),[],[]]
                new_stat_info=self.steps[step+1][key]
                new_stat_info[0].update(last_stat_info[0])
                delta=self.rreduce_weights(fv)
                new_stat_info[1].append([alpha_value+delta,delta,'r',stat])
                betas.append([None,delta,'r',key])
    def update(self,actions,training_step,delta):
        stat=None
        for ind,action in enumerate(actions):
            if ind==0:
                stat=list(self.steps[0].keys())[0]
            print(ind,stat,action)
            data=self.steps[ind][stat]
            fv=self.features(stat)
            betas=data[2]
            print(betas)
            for beta in betas:
                if beta[2]==action:
                    stat=beta[3]
                    break
            
            pass
    @staticmethod
    def result_to_actions(result):
        stack=[]
        actions=[]
        for ind,head in enumerate(result):
            actions.append('s')
            stack.append((ind,result[ind]))
            while len(stack)>=2:
                #print(stack)
                if stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append('l')
                    stack.pop()
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append('r')
                    stack[-2]=stack[-1]
                    stack.pop()
                else:
                    break
        return actions


    @staticmethod
    def actions_to_result(actions):
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

        pass
    def decode(self,raw):
        self.raw=raw
        self.steps=[{} for i in range(2*len(raw))]
        self.steps[0][(0,(None,None))]=[set(),[[0,0,None,None]],[]]
        for i in range(len(raw)*2-1):
            self.find_next(i)
            for k in self.steps[i]:
                #print(i,k)
                pass
        stat=self.find_thrink(len(raw)*2-1)[0]
        #print(stat)
        step=len(raw)*2-1
        actions=[]
        stat_seq=[stat]
        while step:
            alpha=self.steps[step][stat][1][0]
            actions.append(alpha[2])
            debug_betas=self.steps[step-1][alpha[3]][2]
            flag=False
            for beta in debug_betas:
                if beta[2]==alpha[2] and beta[3]==stat:
                    print(step-1,alpha[3],beta)
                    print(step,stat,alpha)
                    print('===')
                    flag=True
                    break
            assert(flag)
            #print(step-1,alpha[3],alpha[2])
            
            stat=alpha[3]
            stat_seq.append([stat,alpha[2]])
            step-=1
        actions.reverse()
        #print(list(enumerate(actions)))
        stat_seq.reverse()
        for ind,x in enumerate(stat_seq):
            print('seq',ind,*x)

        #self.actions_to_result(actions)
        
        stat=None
        for ind,action in enumerate(actions):
            if ind==0:
                stat=list(self.steps[0].keys())[0]
            assert(stat_seq[ind]==[stat,action])
            print(ind,stat,action)
            data=self.steps[ind][stat]
            fv=self.features(stat)
            betas=data[2]
            #print(betas)
            for beta in betas:
                if beta[2]==action and self.steps[ind+1]:
                    stat=beta[3]
                    break
            
            pass
        input()

        
        return actions   
            

def test():
    print('hello')
    raw='abcde'
    stats=Shift_Reduce_Stat()
    actions=stats.decode(raw)
    print(actions)
    result=stats.actions_to_result(actions)

    print(result)
    act=stats.result_to_actions(result)
    print(act)
    pass
def train(training):
    stats=Shift_Reduce_Stat()
    for line in open(training):
        line=line.strip()
        sen=codec.decode(line)
        raw=[(word,tag) for word,tag,_,_ in sen]
        std_result=[x for _,_,x,_ in sen]
        #print(raw)
        rst_actions=stats.decode(raw)
        rst_result=stats.actions_to_result(rst_actions)
        #std_actions=stats.result_to_actions(std_result)
        #print(std_result)
        #print(rst_result)
        #stats.update(rst_actions,3,-1)


if __name__=="__main__":
    pass
