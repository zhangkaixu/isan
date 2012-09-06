import isan.tagging.default_segger as segger
from isan.common.perceptrons import Base_Model as Model
import isan.tagging.dfa as dfa
"""
一个增量搜索模式的中文分词模块
"""


class Segmentation_Space(segger.Segger):
    def __init__(self,beam_width=8):
        self.beam_width=beam_width
        self.weights={}
        self.link()

    def link(self,segger=segger.Segger()):
        self.dfa=dfa.DFA(self,self.beam_width)
        for k,v in self.weights.items():
            self.dfa.set_action(k,v)


    def unlink(self):

        del self.dfa
        self.dfa=None

    def __del__(self):
        self.unlink()


    ### 特征更新相关 
    def update_weights(self,stat,action,delta,step):
        self.dfa.update_action(stat,action,delta,step)


    def average(self,step):
        for k,v in self.dfa.export_weights(step):
            self.weights.setdefault(k,{}).update(v)

    def search(self,raw,Y=None):
        self.set_raw(raw)
        self.set_Y(Y)
        self.dfa.set_raw(raw)
        ret=self.dfa.search(len(raw)+1)
        return ret
    

