#!/usr/bin/python3
import isan.tagging.codec as tagging_codec
import time
import collections
import pickle
import sys

"""
一个增量搜索模式的中文分词模块
"""

def search(raw,action,std_actions=None):
    beam=[action.gen_init_stat()]
    std_stat=[action.gen_init_stat()]
    debug_flag=False
    for k in range(len(raw)+1):
        
        #print(raw[:k],raw[k:])
        #for stat in beam:
        #    print(stat[0],stat[1][0])
        
        new_beam=[]
        if k==0:
            new_beam.append(action.separate(beam[0],raw))
            beam=new_beam
            
        elif k==len(raw):
            for stat in beam:
                new_beam.append(action.separate(stat,raw))
                
            beam=new_beam
            
            
        else:
            for stat in beam:
                new_beam.append(action.separate(stat,raw))
                new_beam.append(action.combine(stat,raw))
            new_beam.sort(reverse=True)
            beam=[]
            last_pos=None
            for stat in new_beam:
                if stat[0]!=last_pos:
                    beam.append(stat)
                    last_pos=stat[0]
            beam.sort(key=lambda x:x[1][0],reverse=True)
            #print(len(beam))
            beam=beam[:min(len(beam),2)]
        
        #early update 似乎不是很好
        #if std_actions:
            #if std_actions[k]=='s':
                #std_stat=action.separate_update(std_stat,raw,0)
            #else:
                #std_stat=action.combine_update(std_stat,raw,0)
            
            #if not any(std_stat[0]==stat[0] 
                    #and 
                    #(std_stat[1][2][0]==stat[1][2][0])
                    #for stat in beam):
                #debug_flag=True
                
                #break
        
    
    
    rst_actions=[]
    beam.sort(key=lambda x:x[1][0],reverse=True)
    stat=beam[0]
    while True:
        if stat[0][-1]==0:break
        rst_actions.append(stat[1][3])
        
        stat=stat[1][2]
    #assert(len(raw)+1==len(rst_actions))
    rst_actions.reverse()

    return rst_actions
    
 
class Features(dict):
    def __init__(self):
        self.acc=dict()
    def __missing__(self,key):
        return 0
    def update(self,feature,delta=0,step=0):
        self.setdefault(feature,0)
        self.acc.setdefault(feature,0)
        self[feature]+=delta
        self.acc[feature]+=step*delta
    def updates(self,features,delta=0,step=0):
        for feature in features:
            self.setdefault(feature,0)
            self.acc.setdefault(feature,0)
            self[feature]+=delta
            self.acc[feature]+=step*delta

    def average(self,step):
        #print(len(self))
        for k in self.acc:
            self[k]=self[k]-self.acc[k]/step
            if self[k]==0:del self[k]
        del self.acc
        #print(len(self))
    
class Sep_Action:
    def __init__(self):
        self.features=Features()
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

#sep_action=Sep_Action()
#com_action=Sep_Action()




class Actions:
    @staticmethod
    def gen_init_stat():
        return [(0,'s','s',0),(0,)]
    
    next_span_s=lambda span:(1,span[2],'s',span[-1]+1)
    next_span_c=lambda span:(span[0]+1,span[2],'c',span[-1]+1)
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

def update(x,std_actions,rst_actions,action,step):
    std_stat=action.gen_init_stat()
    rst_stat=action.gen_init_stat()
    for a,b in zip(rst_actions,std_actions):
        if a =='s':
            std_stat=action.separate_update(std_stat,x,-1,step=step)
        if a=='c':
            std_stat=action.combine_update(std_stat,x,-1,step=step)
        if b =='s':
            rst_stat=action.separate_update(rst_stat,x,1,step=step)
        if b=='c':
            rst_stat=action.combine_update(rst_stat,x,1,step=step)
    
    
def to_set(y):
    offset=0
    s=set()
    for w in y:
        s.add((offset,w))
        offset+=len(w)
    return s
def actions_to_result(actions,raw):
    sen=[]
    cache=''
    for c,a in zip(raw,actions[1:]):
        cache+=c
        if a=='s':
            sen.append(cache)
            cache=''
    return sen
def result_to_actions(y):
    actions=['s']
    for w in y:
        for i in range(len(w)-1):
            actions.append('c')
        actions.append('s')
    return actions
def train():
    actions=Actions()
    step=0
    for it in range(6):
        std,rst,cor=0,0,0
        otime=time.time()
        for line in open("test.tag"):
            step+=1
            sentence=tagging_codec.decode(line.strip())
            
            raw=''.join(x for x,_ in sentence)
            y=[x for x,_ in sentence]
            
            #rst_actions=search(raw,actions)
            
            
            
            std_actions=result_to_actions(y)
            rst_actions=search(raw,actions,std_actions)
            
            hat_y=actions_to_result(rst_actions,raw)
            #hat_y=y
            std+=len(y)
            rst+=len(hat_y)
            cor+=len(to_set(y)&to_set(hat_y))
            
            if std_actions!=rst_actions:
                update(raw,std_actions,rst_actions,actions,step)
            
            
            
            
        p=cor/rst
        r=cor/std
        f=2*p*r/(p+r)
        print(std,rst,cor,f,time.time()-otime)
    actions.sep_action.features.average(step)
    actions.com_action.features.average(step)
    file=open("inc_hyb.model","wb")
    pickle.dump(actions,file)
    
    file.close()
def test():
    file=open("inc_hyb.model","rb")
    actions=pickle.load(file)
    file.close()
    
    std,rst,cor=0,0,0
    otime=time.time()
    for line in open("test.tag"):
        sentence=tagging_codec.decode(line.strip())
        
        raw=''.join(x for x,_ in sentence)
        y=[x for x,_ in sentence]
        std_actions=result_to_actions(y)
        rst_actions=search(raw,actions)
        hat_y=actions_to_result(rst_actions,raw)
        std+=len(y)
        rst+=len(hat_y)
        
        cor+=len(to_set(y)&to_set(hat_y))
        
    p=cor/rst
    r=cor/std
    f=2*p*r/(p+r)
    print(std,rst,cor,f,time.time()-otime)
def predict():
    file=open("inc_hyb.model","rb")
    actions=pickle.load(file)
    file.close()
    for line in sys.stdin:
        raw=line.strip()
        rst_actions=search(raw,actions)
        hat_y=actions_to_result(rst_actions,raw)
        print(tagging_codec.encode(hat_y),file=sys.stdout)
if __name__=="__main__":
    train()
    test()
    
    #predict()
