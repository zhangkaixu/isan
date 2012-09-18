from struct import Struct
import isan.tagging.eval as tagging_eval
import isan.tagging.cwstask as cwstask


"""
You do the best, we do the rest!

来看看如何建造一个中文分词模型
只需要编写最核心的代码，其它代码我都已经编好了
"""
class Segger:
    """告诉isan，这是个什么task"""
    name='中文分词'
    
    """任务的输入和输出是什么，如何从数据文件中获得"""
    class codec:
        """编码、解码"""
        @staticmethod
        def decode(line):
            """从一行文本中，得到输入（raw）和输出（y）"""
            if not line: return []
            seq=[word for word in line.split()]
            raw=''.join(seq)
            return {'raw':raw,
                    'y':seq,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
        def encode():
            pass

    """下面不妨给动作（一个unsigned char类型）定义一下名字
    分词中有两个动作：断与连"""
    sep=11
    com=22

    """告诉isan，有了输入和动作序列，输出该是什么"""
    def actions_to_result(self,actions,raw):
        last_sep=0
        sen=[]
        for i,a in enumerate(actions[1:]):
            if a==self.sep or i==len(actions)-2:
                sen.append(raw[last_sep:i+1])
                last_sep=i+1
        return sen
    
    """有了输出，需要怎样的动作序列才能得到"""
    def result_to_actions(self,y):
        return sum(([self.com]*(len(w)-1)+[self.sep] for w in y),[self.sep])

    """在isan中，状态是一个bytes对象，但Python中tuple好处理一些，
    在此规定一种从tuple到bytes对象的转换规则"""
    stat_fmt=Struct('hcch')

    """分词搜索时的初始状态"""
    init_stat, gen_actions_and_stats,gen_features=cwstask.new()

    """维特比解码中，状态根据动作而转移，
    有了动作序列，就能确定一个状态序列"""
    def actions_to_stats(self,actions):
        stat=self.init_stat
        for action in actions:
            yield stat
            for a,s in self._gen_actions_and_stats(stat):
                if action==a:
                    stat=s
        yield stat

    """根据当前状态，能产生什么动作，并且后续的状态是什么，就由这个函数决定了"""
    def _gen_actions_and_stats(self,stat):
        ind,last,_,wordl,*_=self.stat_fmt.unpack(stat)
        return [(self.sep,self.stat_fmt.pack(ind+1,b'1',last,1)),
                (self.com,self.stat_fmt.pack(ind+1,b'2',last,wordl+1))]

    """这个函数用来在每次新到一个输入的时候，做一些预处理，一般为了加快特征向量生成的速度"""
    def set_raw(self,raw):
        self.raw=raw
        return


    """暂时忽略它"""
    def set_Y(self,Y):
        pass

    """最后告诉isan，如何评价模型的输出和标准答案的输出的好坏。具体可以看这个class"""
    Eval=tagging_eval.TaggingEval
