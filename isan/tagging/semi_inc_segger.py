#!/usr/bin/python3
import collections
import pickle
import sys
import random
import isan.tagging.codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
"""
一个增量搜索模式的中文分词模块
"""

class Defalt_Atom_Action:
    def __init__(self):
        self.features=perceptrons.Features()#特征
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
        self.uni_chars=list('###'+raw+'##')
        self.bi_chars=[(self.uni_chars[i],self.uni_chars[i+1]) for i in range(len(self.uni_chars)-1)]
    def _key_gen(self,span):
        raw=self.raw
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars
        c_ind=span[0]+2
        ws_current=span[1]
        ws_left=span[2]
        
        fv=[
                ("ws",ws_left,ws_current),
                ("c",uni_chars[c_ind],ws_current),
                ("r",uni_chars[c_ind+1],ws_current),
                ('l',uni_chars[c_ind-1],ws_current),
                ("cr",bi_chars[c_ind],ws_current),
                ("lc",bi_chars[c_ind-1],ws_current),
                ("rr2",bi_chars[c_ind+1],ws_current),
                ("l2l",bi_chars[c_ind-2],ws_current),
            ]
        if len(span)>=4:
            w_current=raw[span[0]+1-span[3]:span[0]+1]
            fv.append(("w",w_current))
        return fv
        
    def __call__(self,stat):
        """
        返回一个动作的分数
        """
        return sum(self.features.get(cur,0) for cur in self._key_gen(stat[0]))

    def update(self,stat,delta,step=0):
        """
        跟新权重
        """
        self.features.updates(self._key_gen(stat[0]),delta,step)


class Defalt_Position:
    def __call__(self,last=None,action=None):
        if not last:
            return (0,'|','|',0)#(当前位置，上一个动作，上上个动作，到前一个断开的距离)
        if action=='s':
            return (last[0]+1,'s',last[1],1)
        else:
            return (last[0]+1,'c',last[1],last[-1]+1)
    def is_init(self,pos):
        return pos[0]==0

class Character_Labeling_Based_Position:
    def __call__(self,last=None,action=None):
        if not last:
            return (0,'|','|')#(当前位置，上一个动作，上上个动作)
        if action=='s':
            return (last[0]+1,'s',last[1])
        else:
            return (last[0]+1,'c',last[1])
    def is_init(self,pos):
        return pos[0]==0


class Defalt_Actions:
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

    def gen_init_stat(self):
        return [self.positions(),(0,)]
    
    def __init__(self,
                atom_action=Defalt_Atom_Action,
                positions=Defalt_Position):
        self.sep_action=atom_action()
        self.com_action=atom_action()
        self.positions=positions()
        self.max_pos_size=1
    def search(self,raw,search_space=None):
        self.sep_action.set_raw(raw)
        self.com_action.set_raw(raw)
        beam=[self.gen_init_stat()]
        std_stat=[self.gen_init_stat()]
        debug_flag=False
        for k in range(len(raw)+1):
            new_beam=[]
            if k==0:
                new_beam.append(self._separate(beam[0]))
                beam=new_beam
            elif k==len(raw):
                for stat in beam:
                    new_beam.append(self._separate(stat))
                beam=new_beam
            else:
                for stat in beam:
                    if not search_space:
                        new_beam.append(self._separate(stat))
                        new_beam.append(self._combine(stat))
                    else:
                        if 's' in search_space[k]:
                            new_beam.append(self._separate(stat))
                        if 'c' in search_space[k]:
                            new_beam.append(self._combine(stat))

                new_beam.sort(reverse=True)
                beam=[]

                #确保每个状态只保留一个最优的解
                last_pos=None
                pos_size=0
                for stat in new_beam:
                    if stat[0]!=last_pos:
                        beam.append(stat)
                        last_pos=stat[0]
                        pos_size=1
                    else:
                        if pos_size>= self.max_pos_size : continue
                        pos_size+=1
                        beam.append(stat)


                #保留一定宽度的解（柱宽度）
                beam.sort(key=lambda x:x[1][0],reverse=True)
                beam=beam[:min(len(beam),2)]

        beam.sort(key=lambda x:x[1][0],reverse=True)
        
        self.delta=-1
        if len(beam)>1:
            self.delta=beam[0][1][0]-beam[1][1][0]
        #print(raw)
        #print(delta)
        
        rst_actions=[]
        stat=beam[0]
        while True:
            if self.positions.is_init(stat[0]):break
            rst_actions.append(stat[1][2])
            stat=stat[1][1]
        rst_actions.reverse()

        return rst_actions


    def update(self,x,std_actions,rst_actions,step):
        std_stat=self.gen_init_stat()
        rst_stat=self.gen_init_stat()
        for a,b in zip(rst_actions,std_actions):
            if a=='s':
                std_stat=self._separate_update(std_stat,-1,step=step)
            if a=='c':
                std_stat=self._combine_update(std_stat,-1,step=step)
            if b=='s':
                rst_stat=self._separate_update(rst_stat,1,step=step)
            if b=='c':
                rst_stat=self._combine_update(rst_stat,1,step=step)
    def average(self,step):
        self.sep_action.features.average(step)
        self.com_action.features.average(step)
        
    ### 私有函数 
    def _separate(self,stat):
        return [self.positions(stat[0],'s'),
                (stat[1][0]+self.sep_action(stat),stat,'s')]
    def _separate_update(self,stat,delta,step=0):
        self.sep_action.update(stat,delta,step)
        return [self.positions(stat[0],'s'),
                (0,stat,'s')]


    def _combine(self,stat):
        return [self.positions(stat[0],'c'),
                (stat[1][0]+self.com_action(stat),stat,'c')]
    def _combine_update(self,stat,delta,step=0):
        self.com_action.update(stat,delta,step)
        return [self.positions(stat[0],'c'),
                (0,stat,'c')]



class Model:
    """
    模型
    """
    def __init__(self,model_file,actions=None):
        """
        初始化
        actions： 如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        if actions==None:
            file=open(model_file,"rb")
            self.actions=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.actions=actions
            self.step=0
            
    def __call__(self,raw):
        """
        解码，读入生句子，返回词的数组
        """
        rst_actions=self.actions.search(raw)
        hat_y=self.actions.actions_to_result(rst_actions,raw)
        return hat_y
    def _learn_sentence(self,raw,std_space):
        """
        学习，根据生句子和标准分词结果
        """
        self.step+=1#学习步数加一
        #print(raw)
        #print(std_space)
        std_actions=self.actions.search(raw,std_space)#得到标准动作
        rst_actions=self.actions.search(raw)#得到解码后动作
        hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
        if std_actions!=rst_actions:#如果动作不一致，则更新
            self.actions.update(raw,std_actions,rst_actions,self.step)
        return hat_y
    def save(self):
        """
        保存模型
        """
        self.actions.average(self.step)
        file=open(self.model_file,'wb')
        pickle.dump(self.actions,file)
        file.close()
    def train(self,training_file,iteration=5):
        """
        训练
        """
        training_data=[]
        for line in open(training_file):
            y=tagging_codec.decode(line.strip())
            
            std_actions=self.actions.result_to_actions(y)#得到标准动作
            std_space=[[x] for x in std_actions]
            for i in range(len(std_space)):
                if random.random()<0:
                    std_space[i]=['s','c']
            if random.random()<0.1:
                training_data.append((''.join(y),y,std_space))
            #print(y)
        #training_data=training_data[:int(len(training_data)*0.7)]
        for it in range(iteration):#迭代整个语料库
            eval=tagging_eval.TaggingEval()#测试用的对象
            for raw,y,std_space in training_data:#迭代每个句子
                hat_y=self._learn_sentence(raw,std_space)
                eval(y,hat_y)#学习它
            eval.print_result()#打印评测结果
    def test(self,test_file):
        """
        测试
        """
        eval=tagging_eval.TaggingEval()
        for line in open(test_file):
            y=tagging_codec.decode(line.strip())
            raw=''.join(y)
            hat_y=self(raw)
            eval(y,hat_y)
            #print(raw,self.actions.delta)
            #if not y==hat_y:
            #    input()
        eval.print_result()
if __name__=="__main__":
    train()
    test()
