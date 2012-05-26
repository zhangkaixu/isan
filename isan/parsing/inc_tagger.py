#!/usr/bin/python3
import pickle
import sys


import isan.common.perceptrons as perceptrons
"""
一个增量搜索模式的中文分词模块
"""

    
 

    
class Defalt_Action:
    def __init__(self):
        self.features=perceptrons.Features()
    def set_raw(self,raw):
        self.raw=raw
        self.uni_chars=list('###'+raw+'##')
        self.bi_chars=[(self.uni_chars[i],self.uni_chars[i+1]) for i in range(len(self.uni_chars)-1)]
    def _gen_keys(self,span):
        raw=self.raw
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars
        w_current=raw[span[3]+1-span[0]:span[3]+1]
        ws_current=span[2]
        ws_left=span[1]
        c_ind=span[3]-1+3
        #print(w_current in self.dic,w_current)
        #if ("ass" in self.__dict__):
            
            #return (
                #("w",w_current),
                #("try",ws_left,ws_current,self.bk[span[3]]),
                #("ws",ws_left,ws_current),
                #("c",uni_chars[c_ind],ws_current),
                #("r",uni_chars[c_ind+1],ws_current),
                #('l',uni_chars[c_ind-1],ws_current),
                #("cr",bi_chars[c_ind],ws_current),
                #("lc",bi_chars[c_ind-1],ws_current),
                #("rr2",bi_chars[c_ind+1],ws_current),
                #("l2l",bi_chars[c_ind-2],ws_current),
            #)
        return (
                ("w",w_current),
                
                ("ws",ws_left,ws_current),
                ("c",uni_chars[c_ind],ws_current),
                ("r",uni_chars[c_ind+1],ws_current),
                ('l',uni_chars[c_ind-1],ws_current),
                ("cr",bi_chars[c_ind],ws_current),
                ("lc",bi_chars[c_ind-1],ws_current),
                ("rr2",bi_chars[c_ind+1],ws_current),
                ("l2l",bi_chars[c_ind-2],ws_current),
            )
        
        
    def __call__(self,stat):
        score=sum(self.features.get(cur,0) for cur in self._gen_keys(stat[0]))
        return score
    def update(self,stat,delta,step=0):
        self.features.updates(self._gen_keys(stat[0]),delta,step)





class Defalt_Actions:
    @staticmethod
    def gen_init_stat():
        return [(0,'|','|',0),(0,)]
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
    
    def __init__(self,atom_action=Defalt_Action):
        self.sep_action=atom_action();
        self.com_action=atom_action();
    
    

    def search(self,raw,std_actions=None):
        self.sep_action.set_raw(raw)
        self.com_action.set_raw(raw)
        beam=[self.gen_init_stat()]
        std_stat=[self.gen_init_stat()]
        debug_flag=False
        for k in range(len(raw)+1):
            new_beam=[]
            if k==0:
                new_beam.append(self.separate(beam[0]))
                beam=new_beam
            elif k==len(raw):
                for stat in beam:
                    new_beam.append(self.separate(stat))
                beam=new_beam
            else:
                for stat in beam:
                    new_beam.append(self.separate(stat))
                    new_beam.append(self.combine(stat))
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
                std_stat=self.separate_update(std_stat,-1,step=step)
            if a=='c':
                std_stat=self.combine_update(std_stat,-1,step=step)
            if b =='s':
                rst_stat=self.separate_update(rst_stat,1,step=step)
            if b=='c':
                rst_stat=self.combine_update(rst_stat,1,step=step)
    def average(self,step):
        self.sep_action.features.average(step)
        self.com_action.features.average(step)
        
    
    def separate(self,stat):
        return [(1,stat[0][2],'s',stat[0][-1]+1),
                (stat[1][0]+self.sep_action(stat),stat,stat,'s')]
    def separate_update(self,stat,delta,step=0):
        self.sep_action.update(stat,delta,step)
        return [(1,stat[0][2],'s',stat[0][-1]+1),
                (0,stat,stat,'s')]


    def combine(self,stat):
        return [(stat[0][0]+1,stat[0][2],'c',stat[0][-1]+1),
                (stat[1][0]+self.com_action(stat),stat[1][1],stat,'c')]
    
    def combine_update(self,stat,delta,step=0):
        self.com_action.update(stat,delta,step)
        return [(stat[0][0]+1,stat[0][2],'c',stat[0][-1]+1),
                (0,stat[1][1],stat,'c')]



class Model:
    def __init__(self,model_file,actions=None):
        if actions==None:
            file=open(model_file,"rb")
            self.actions=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.actions=actions
            self.step=0
            
    def __call__(self,raw):
        rst_actions=self.actions.search(raw)
        hat_y=self.actions.actions_to_result(rst_actions,raw)
        return hat_y
    def learn(self,raw,y):
        self.step+=1
        std_actions=self.actions.result_to_actions(y)
        rst_actions=self.actions.search(raw)
        
        hat_y=self.actions.actions_to_result(rst_actions,raw)
        
        if std_actions!=rst_actions:
            self.actions.update(raw,std_actions,rst_actions,self.step)
        return hat_y
    def save(self):
        self.actions.average(self.step)
        file=open(self.model_file,'wb')
        pickle.dump(self.actions,file)
        file.close()
    def train(self,training_file,iteration=5):
        for it in range(iteration):
            eval=tagging_eval.TaggingEval()
            for line in open(training_file):
                y=tagging_codec.decode(line.strip())
                raw=''.join(y)
                eval(y,self.learn(raw,y))
            eval.print_result()
    def test(self,test_file):
        eval=tagging_eval.TaggingEval()
        for line in open(test_file):
            y=tagging_codec.decode(line.strip())
            raw=''.join(y)
            eval(y,self(raw))
        eval.print_result()
if __name__=="__main__":
    train()
    test()
