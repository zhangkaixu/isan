#!/usr/bin/python3
import pickle
import sys

import isan.tagging.codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
"""
一个增量搜索模式的中文分词模块
"""

    
 

    
class Sep_Action:
    def __init__(self):
        self.features=perceptrons.Features()
    def _gen_keys(self,span,raw):
        w_current=raw[span[3]+1-span[0]:span[3]+1]
        #last_word=raw[span[0]:span[1]]

        c_right=raw[span[3]] if span[3]<len(raw) else '#'
        c_right2=raw[span[3]+1] if span[3]+1<len(raw) else '#'
        c_current=raw[span[3]-1] if span[3]-1>=0 else '#'
        c_left=raw[span[3]-2] if span[3]-2>=0 else '#'
        c_left2=raw[span[3]-3] if span[3]-3>=0 else '#'
        ws_current=span[2]
        ws_left=span[1]
        return (
                ("w",w_current),
                ("ws",ws_left,ws_current),
                ("c",c_current,ws_current),
                ("r",c_right,ws_current),
                ('l',c_left,ws_current),
                ("cr",c_current,c_right,ws_current),
                ("lc",c_left,c_current,ws_current),
                ("rr2",c_right,c_right2,ws_current),
                ("l2l",c_left2,c_left,ws_current),
            )
        
    def __call__(self,stat,raw):
        score=sum(self.features.get(cur,0) for cur in self._gen_keys(stat[0],raw))
        return score
    def update(self,stat,raw,delta,step=0):
        self.features.updates(self._gen_keys(stat[0],raw),delta,step)





class Actions:
    @staticmethod
    def gen_init_stat():
        return [(0,'s','s',0),(0,)]
    @staticmethod
    def actions_to_result(actions,raw):
        sen=[]
        cache=''
        for c,a in zip(raw,actions[1:]):
            cache+=c
            if a=='s':
                sen.append(cache)
                cache=''
        return sen
    @staticmethod
    def result_to_actions(y):
        actions=['s']
        for w in y:
            for i in range(len(w)-1):
                actions.append('c')
            actions.append('s')
        return actions
    
    def __init__(self):
        self.sep_action=Sep_Action();
        self.com_action=Sep_Action();
    
    def separate(self,stat,raw):
        return [(1,stat[0][2],'s',stat[0][-1]+1),
                (stat[1][0]+self.sep_action(stat,raw),stat,stat,'s')]
    def separate_update(self,stat,raw,delta,step=0):
        self.sep_action.update(stat,raw,delta,step)
        return [(1,stat[0][2],'s',stat[0][-1]+1),
                (0,stat,stat,'s')]


    def combine(self,stat,raw):
        return [(stat[0][0]+1,stat[0][2],'c',stat[0][-1]+1),
                (stat[1][0]+self.com_action(stat,raw),stat[1][1],stat,'c')]
    
    def combine_update(self,stat,raw,delta,step=0):
        self.com_action.update(stat,raw,delta,step)
        return [(stat[0][0]+1,stat[0][2],'c',stat[0][-1]+1),
                (0,stat[1][1],stat,'c')]

    def search(self,raw,std_actions=None):
        beam=[self.gen_init_stat()]
        std_stat=[self.gen_init_stat()]
        debug_flag=False
        for k in range(len(raw)+1):
            new_beam=[]
            if k==0:
                new_beam.append(self.separate(beam[0],raw))
                beam=new_beam
                
            elif k==len(raw):
                for stat in beam:
                    new_beam.append(self.separate(stat,raw))
                    
                beam=new_beam
                
                
            else:
                for stat in beam:
                    new_beam.append(self.separate(stat,raw))
                    new_beam.append(self.combine(stat,raw))
                new_beam.sort(reverse=True)
                beam=[]
                last_pos=None
                for stat in new_beam:
                    if stat[0]!=last_pos:
                        beam.append(stat)
                        last_pos=stat[0]
                beam.sort(key=lambda x:x[1][0],reverse=True)
                beam=beam[:min(len(beam),2)]

        rst_actions=[]
        beam.sort(key=lambda x:x[1][0],reverse=True)
        stat=beam[0]
        while True:
            if stat[0][-1]==0:break
            rst_actions.append(stat[1][3])
            stat=stat[1][2]
        rst_actions.reverse()

        return rst_actions



    def update(self,x,std_actions,rst_actions,step):
        std_stat=self.gen_init_stat()
        rst_stat=self.gen_init_stat()
        for a,b in zip(rst_actions,std_actions):
            if a =='s':
                std_stat=self.separate_update(std_stat,x,-1,step=step)
            if a=='c':
                std_stat=self.combine_update(std_stat,x,-1,step=step)
            if b =='s':
                rst_stat=self.separate_update(rst_stat,x,1,step=step)
            if b=='c':
                rst_stat=self.combine_update(rst_stat,x,1,step=step)
    



class Model:
    def __init__(self,model_file,mode='r'):
        self.mode=mode
        if self.mode=='r':
            file=open(model_file,"rb")
            self.actions=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.actions=Actions()
            self.step=0
            
    def __call__(self,raw):
        rst_actions=self.actions.search(raw)
        #rst_actions=search(raw,self.actions)
        hat_y=Actions.actions_to_result(rst_actions,raw)
        return hat_y
    def learn(self,raw,y):
        self.step+=1
        std_actions=Actions.result_to_actions(y)
        rst_actions=self.actions.search(raw)
        
        hat_y=Actions.actions_to_result(rst_actions,raw)
        
        if std_actions!=rst_actions:
            self.actions.update(raw,std_actions,rst_actions,self.step)
        return hat_y
    def save(self):
        self.actions.sep_action.features.average(self.step)
        self.actions.com_action.features.average(self.step)
        file=open(self.model_file,'wb')
        pickle.dump(self.actions,file)
        file.close()
    def train(self,training_file,iteration=5):
        eval=tagging_eval.TaggingEval()
        for it in range(iteration):
            eval=tagging_eval.TaggingEval()
            for line in open(training_file):
                sentence=tagging_codec.decode(line.strip())
                raw=''.join(x for x in sentence)
                y=[x for x in sentence]
                eval(y,self.learn(raw,y))
            eval.print_result()
        #self.save()
    def test(self,test_file):
        eval=tagging_eval.TaggingEval()
        for line in open(test_file):
            sentence=tagging_codec.decode(line.strip())
            
            raw=''.join(x for x in sentence)
            y=[x for x in sentence]
            
            hat_y=self(raw)
            eval(y,hat_y)
    
        eval.print_result()
if __name__=="__main__":
    train()
    test()
