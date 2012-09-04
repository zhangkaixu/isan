import collections
import pickle
import sys
import struct
import isan.tagging.cws_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.tagging.dfabeam as dfabeam
import isan.tagging.default_segger as segger
from isan.common.perceptrons import Base_Model as Model
"""
一个增量搜索模式的中文分词模块
"""


class Segmentation_Space:
    def __init__(self,beam_width=8):
        self.beam_width=beam_width
        self.weights={}
        self.link()

    def link(self,segger=segger.Segger()):
        self.segger=segger
        func_list={
                'init_stat': None,
                'stat_fmt_str': None,
                'actions_to_result': None,
                'result_to_actions': None,
                'gen_actions_and_stats': None,
                'gen_features': None,
                'actions_to_stats':self._actions_to_stats,
                }
        for func,dft_attr in func_list.items():
            if hasattr(self.segger,func):
                setattr(self,func,getattr(self.segger,func))
            else:
                setattr(self,func,dft_attr)
                
        self.dfabeam=dfabeam.new(
                self.beam_width,
                #None,
                self.init_stat,
                #None,
                self.gen_actions_and_stats,
                #None,
                self.gen_features,
                )
        for k,v in self.weights.items():
            dfabeam.set_action(self.dfabeam,k,v)

        self.codec=tagging_codec
        self.Eval=tagging_eval.TaggingEval

    def unlink(self):
        self.actions_to_result=None
        self.result_to_actions=None
        self.actions_to_stats=None
        self.gen_actions_and_stats=None
        self.gen_features=None
        self.stat_fmt=None
        self.segger=None
        self.codec=None
        self.Eval=None

    def __del__(self):
        dfabeam.delete(self.dfabeam)

    #特征相关
    def set_raw(self,raw):
        self.segger.set_raw(raw)

    ### 特征更新相关 
    def update(self,x,std_actions,rst_actions,step):
        self._update_actions(std_actions,1,step)
        self._update_actions(rst_actions,-1,step)
    def _update_actions(self,actions,delta,step):
        for stat,action in zip(self.actions_to_stats(actions),actions,):
            dfabeam.update_action(self.dfabeam,stat,action,delta,step)
   

    def average(self,step):
        for k,v in dfabeam.export_weights(self.dfabeam,step):
            self.weights.setdefault(k,{}).update(v)

    def search(self,raw):
        self.set_raw(raw)
        dfabeam.set_raw(self.dfabeam,raw)
        ret=dfabeam.search(self.dfabeam,len(raw)+1)
        return ret
    

    def _actions_to_stats(self,actions):
        stat=self.init_stat
        for action in actions:
            yield stat
            for a,s in self.gen_actions_and_stats(stat):
                if action==a:
                    stat=s
        yield stat

