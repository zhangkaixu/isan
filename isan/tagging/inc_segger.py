import collections
import pickle
import sys
import struct
import isan.tagging.cws_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
import isan.tagging.dfabeam as dfabeam
"""
一个增量搜索模式的中文分词模块
"""

class Actions:
    sep='s'
    com='c'
    def __init__(self):
        self.actions=[self.sep,self.com]
    def as_result(self,actions,raw):
        sen=[]
        cache=''
        for c,a in zip(raw,actions[1:]):
            cache+=c
            if a==self.sep:
                sen.append(cache)
                cache=''
        if cache:
            sen.append(cache)
        return sen
    def from_result(self,y):
        actions=[self.sep]
        for w in y:
            for i in range(len(w)-1):
                actions.append(self.com)
            actions.append(self.sep)
        return actions
class Stats(Actions):
    def __init__(self):
        self.fmt="hcch"
        self.init=(0,b'|',b'|',0)
        
    def from_actions(self,actions):
        stat=self.init
        for action in actions:
            yield stat
            ind,last,_,wordl=stat
            if action==self.sep:
                stat=(ind+1,b's',last,1)
            else:
                stat=(ind+1,b'c',last,wordl+1)
        yield stat
    def gen_stats(self,stat):
        ind,last,_,wordl=stat
        return [(self.sep,(ind+1,b's',last,1)),
                (self.com,(ind+1,b'c',last,wordl+1))]

class Features:
    def set_raw(self,raw):
        self.raw=raw
        self.uni_chars=list(x.encode() for x in '###'+raw+'##')
        self.bi_chars=[self.uni_chars[i]+self.uni_chars[i+1]
                for i in range(len(self.uni_chars)-1)]
    def gen_features(self,span):
        raw=self.raw
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars

        c_ind=span[0]+2
        ws_current=span[1]
        ws_left=span[2]
        w_current=raw[span[0]-span[3]:span[0]]
        fv=[ 
                b'0'+ws_current+ws_left,
                b"1"+uni_chars[c_ind]+ws_current,
                b"2"+uni_chars[c_ind+1]+ws_current,
                b'3'+uni_chars[c_ind-1]+ws_current,
                b"a"+bi_chars[c_ind]+ws_current,
                b"b"+bi_chars[c_ind-1]+ws_current,
                b"c"+bi_chars[c_ind+1]+ws_current,
                b"d"+bi_chars[c_ind-2]+ws_current,
                b"w"+w_current.encode(),
                ]
        return fv



class Segmentation_Space:
    default_conf={
            'actions':Actions(),
            'stats':Stats(),
            'features':Features(),
            'beam_width':8,
            }
    def __init__(self,beam_width=8,conf=default_conf):
        self.conf=self.default_conf
        self.beam_width=self.conf['beam_width']
        self.actions={a:{} for a in self.conf['actions'].actions}
        self.link()

    def link(self):
        self.stat_fmt=struct.Struct(self.conf['stats'].fmt)
        self.init=self.stat_fmt.pack(*self.conf['stats'].init)
        self.actions_to_stats=self.conf['stats'].from_actions
        self.gen_stats=self.conf['stats'].gen_stats
        self.actions_to_result=self.conf['actions'].as_result
        self.result_to_actions=self.conf['actions'].from_result
        self.gen_features=self.conf['features'].gen_features
        self.dfabeam=dfabeam.new(
                self.beam_width,
                #None,
                self.init,
                #None,
                lambda x: [(a,self.stat_fmt.pack(*k))
                    for a,k in 
                        self.gen_stats(self.stat_fmt.unpack(x))],
                #None,
                lambda x: self.gen_features(self.stat_fmt.unpack(x)),
                )
        for k,v in self.actions.items():
            dfabeam.set_action(self.dfabeam,k,v)


    def unlink(self):
        self.actions_to_result=None
        self.result_to_actions=None
        self.actions_to_stats=None
        self.gen_stats=None
        self.gen_features=None
        self.stat_fmt=None

    def __del__(self):
        dfabeam.delete(self.dfabeam)

    #特征相关
    def set_raw(self,raw):
        self.conf['features'].set_raw(raw)

    ### 特征更新相关 
    def update(self,x,std_actions,rst_actions,step):
        self._update_actions(std_actions,1,step)
        self._update_actions(rst_actions,-1,step)
    def _update_actions(self,actions,delta,step):
        for stat,action in zip(self.actions_to_stats(actions),actions,):
            stat=self.stat_fmt.pack(*stat)
            dfabeam.update_action(self.dfabeam,stat,action,delta,step)
   

    def average(self,step):
        for k,v in self.actions.items():
            v.update(dfabeam.export_weights(self.dfabeam,step,k))

    def search(self,raw):
        self.set_raw(raw)
        dfabeam.set_raw([self.dfabeam,raw])
        ret=dfabeam.search([self.dfabeam,len(raw)+1])
        return ret


class Model(perceptrons.Base_Model):
    """
    模型
    """
    def __init__(self,model_file,schema=None):
        """
        初始化
        """
        super(Model,self).__init__(model_file,schema)
        self.codec=tagging_codec
        self.Eval=tagging_eval.TaggingEval

