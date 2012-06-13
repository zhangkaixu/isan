#!/usr/bin/python3
import collections
import pickle
import sys
import random
import isan.common.perceptrons as perceptrons
"""
"""

class Defalt_Atom_Action:
    def __init__(self):
        self.features=perceptrons.Features()#特征
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
        pass
    def _key_gen(self,stat):
        ind,stack_top=stat
        top1,top2=stack_top
        
        fv=[('s1',top1[2]),
                ('s2',top2[2])]
        return fv
        
    def __call__(self,stat):
        """
        返回一个动作的分数
        """
        return sum(self.features.get(cur,0) for cur in self._key_gen(stat))

    def update(self,stat,delta,step=0):
        """
        更新权重
        """
        self.features.updates(self._key_gen(stat),delta,step)
        
class Shift_Reduce_Stat:
    """
    步数 :
    (解析位置, (栈顶若干元素)) :
    [set(predictors),alphas,betas]
        alpha=(score,step_score,action,last_stat)
    """
    def __init__(self,raw):
        self.raw=raw
        self.steps=[{} for i in range(2*len(raw))]
        self.steps[0][(0,(None,None))]=[set(),[[0,0,None,None]],[]]
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
            stats._gen_next(step,k)
    
    def _gen_next(self,step,stat):
        ind,stack_top=stat
        predictors,alphas,betas=self.steps[step][stat]
        #shift
        if ind<len(self.raw):
            key=(ind+1,((ind,ind+1,self.raw[ind]),stack_top[0]))
            if key not in self.steps[step+1]:
                self.steps[step+1][key]=[set(),[],[]]
            new_stat_info=self.steps[step+1][key]
            new_stat_info[0].add((step,stat))
            new_stat_info[1].append([None,0,'s',stat])
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
                new_stat_info[1].append([None,0,'l',stat])

                #right-reduce
                key=(ind,((left[0],right[1],right[2]),predictor[1][1]))
                if key not in self.steps[step+1]:
                    self.steps[step+1][key]=[set(),[],[]]
                new_stat_info=self.steps[step+1][key]
                new_stat_info[0].update(last_stat_info[0])
                new_stat_info[1].append([None,0,'r',stat])
if __name__=="__main__":
    print('hello')
    raw='abcde'
    stats=Shift_Reduce_Stat(raw)
    for i in range(len(raw)*2-1):
        stats.find_next(i)
        for k in stats.steps[i]:
            print(i,k)

    pass
