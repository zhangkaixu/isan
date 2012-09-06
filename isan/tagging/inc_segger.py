import isan.tagging.default_segger as segger
from isan.common.perceptrons import Base_Model as Model
import isan.tagging.dfa as dfa
"""
一个增量搜索模式的中文分词模块
"""


class Segmentation_Space:
    def __init__(self,beam_width=8):
        self.func_list={
                'init_stat': None,
                'actions_to_result': None,
                'result_to_actions': None,
                'actions_to_stats':"_actions_to_stats",
                'gen_actions_and_stats': None,
                'gen_features': None,
                'codec': None,
                'Eval': None,
                }

        self.beam_width=beam_width
        self.weights={}
        self.link()

    def link(self,segger=segger.Segger()):
        self.segger=segger
        for func,dft_attr in self.func_list.items():
            if hasattr(self.segger,func):
                setattr(self,func,getattr(self.segger,func))
            else:
                setattr(self,func,getattr(self,dft_attr))
                
        self.dfa=dfa.DFA(self,self.beam_width)
        for k,v in self.weights.items():
            self.dfa.set_action(k,v)


    def unlink(self):
        for func in self.func_list:
            if hasattr(self,func):
                delattr(self,func)
        self.segger=None

        del self.dfa
        self.dfa=None

    def __del__(self):
        self.unlink()

    #特征相关
    def set_raw(self,raw):
        self.segger.set_raw(raw)

    ### 特征更新相关 
    def update(self,x,std_actions,rst_actions,step):
        self._update_actions(std_actions,1,step)
        self._update_actions(rst_actions,-1,step)
    def _update_actions(self,actions,delta,step):
        for stat,action in zip(self.actions_to_stats(actions),actions,):
            self.dfa.update_action(stat,action,delta,step)
   

    def average(self,step):
        for k,v in self.dfa.export_weights(step):
            self.weights.setdefault(k,{}).update(v)

    def search(self,raw,Y=None):
        self.set_raw(raw)
        self.segger.set_Y(Y)
        self.dfa.set_raw(raw)
        ret=self.dfa.search(len(raw)+1)
        return ret
    

    def _actions_to_stats(self,actions):
        stat=self.init_stat
        for action in actions:
            yield stat
            for a,s in self.gen_actions_and_stats(stat):
                if action==a:
                    stat=s
        yield stat

