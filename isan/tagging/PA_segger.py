from struct import Struct
import isan.tagging.eval as tagging_eval
import isan.tagging.cwstask as cwstask
import isan.tagging.cws as cws
import json
import random

"""
You do the best, we do the rest!

来看看如何建造一个中文分词模型
只需要编写最核心的代码，其它代码我都已经编好了
"""
class Segger(cws.Task):
    """告诉isan，这是个什么task"""
    name='局部标注中文分词'
    
    class codec(cws.Task.codec):
        """
        任务的输入和输出是什么，如何从数据文件中获得
        """
        @staticmethod
        def decode(line):
            """
            编码、解码
            从一行文本中，得到输入（raw）和输出（y）
            """
            line=line.strip()
            if not line: return []
            if line[0]=='{':
                data=json.loads(line)
                #if data['Y_b'][1] : return []
                return data
            seq=[word for word in line.split()]
            raw=''.join(seq)
            
            return {'raw':raw,
                    'y':seq,
                    'Y_a' : None,
                    'Y_b' : None,
                    }

    def is_belong(self,actions,Y):
        seq,intervals=Y
        
        if intervals :
            offset=0
            y=self.actions_to_result(actions)
            for w in y:
                r=intervals[offset][1]
                if r!=-1 and offset+len(w)>r : 
                    #print(y)
                    return False
                l=intervals[offset+len(w)][0]
                if l!=-1 and l>offset : return False
                offset+=len(w)
            return True
        if seq:
            for a,s in zip(actions,seq):
                if s and ((s=='s' and a!=self.sep) or (s=='c' and a!=self.com)) : 
                    return False
            return True

    def gen_actions_and_stats(self,stat):
        """
        根据当前状态，能产生什么动作，并且后续的状态是什么，就由这个函数决定了
        """
        ind,last,_,wordl,lwordl=self.stat_fmt.unpack(stat)
        if self.actions and self.actions[ind]:
            if self.actions[ind]=='s':
                return [(self.sep,self.stat_fmt.pack(ind+1,b'1',last,1,wordl))]
            else :
                return [(self.com,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]
        if self.intervals :
            rtn=[]
            ll,lr=self.intervals[ind-wordl]
            rl,rr=self.intervals[ind]
            if lr!=-1 and lr<=ind :
                return [(self.sep,self.stat_fmt.pack(ind+1,b'1',last,1,wordl))]
            if rl!=-1 and ind-wordl<rl :
                return [(self.com,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]
        return [(self.sep,self.stat_fmt.pack(ind+1,b'1',last,1,wordl)),
                (self.com,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]

    def init(self):
        """
        分词搜索时的初始状态
        """
        #self.init_stat,self.gen_actions_and_stats,self.gen_features=cwstask.new()
        _,_,self.gen_features=cwstask.new()
        pass

    def set_raw(self,raw,Y=None):
        """
        这个函数用来在每次新到一个输入的时候，做一些预处理，一般为了加快特征向量生成的速度
        """
        if Y:
            self.actions,self.intervals=Y
        else :
            self.actions,self.intervals=None,None

