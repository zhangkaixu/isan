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
        
class Segmentation_Space:
    
    default_conf={
            'init':struct.pack("hcch",0,b'|',b'|',0),
            'state_gen':None,
            'feature_gen':None,
            'beam_width':8,

            }
    def __init__(self,beam_width=8):
        self.conf=self.default_conf
        self.init=self.conf['init']
        self.beam_width=self.conf['beam_width']
        self.actions={'s':{},'c':{}}
        self.link_c()
    def link_c(self):
        self.dfabeam=dfabeam.new(
                self.init,
                self.beam_width,
                #None,
                self.keygen_for_c,
                #None,
                self.gen_feature,
                )
        dfabeam.set_action(self.dfabeam,'s',self.actions['s'])
        dfabeam.set_action(self.dfabeam,'c',self.actions['c'])



    def __del__(self):
        dfabeam.delete(self.dfabeam)

    @staticmethod
    def actions_to_result(actions,raw):
        sen=[]
        cache=''
        for c,a in zip(raw,actions[1:]):
            cache+=c
            if a=='s':
                sen.append(cache)
                cache=''
        if cache:
            sen.append(cache)
        return sen
    @staticmethod
    def result_to_actions(y):
        actions=['s']
        for w in y:
            for i in range(len(w)-1):
                actions.append('c')
            actions.append('s')
        return actions
    
    def _actions_to_stats(self,actions):
        stat=self.init
        stat=struct.unpack("hcch",stat)
        for action in actions:
            yield stat
            ind,last,_,wordl=stat
            if action=='s':
                stat=(ind+1,b's',last,1)
            else:
                stat=(ind+1,b'c',last,wordl+1)
        yield stat
    def average(self,step):
        self.actions['s'].update(dfabeam.export_weights(self.dfabeam,step,'s'))
        self.actions['c'].update(dfabeam.export_weights(self.dfabeam,step,'c'))
        pass
    def update(self,x,std_actions,rst_actions,step):
        self._update_actions(std_actions,1,step)
        self._update_actions(rst_actions,-1,step)
    ### 私有函数 
    def _update_actions(self,actions,delta,step):
        for stat,action in zip(self._actions_to_stats(actions),actions,):
            stat=struct.pack("hcch",*stat)
            dfabeam.update_action([self.dfabeam,stat,action,delta,step])
   
    def keygen_for_c(self,stat):
        stat=struct.unpack("hcch",stat)
        ind,last,_,wordl=stat
        nexts=[]
        nexts.append(('s',struct.pack("hcch",ind+1,b's',last,1)))
        nexts.append(('c',struct.pack("hcch",ind+1,b'c',last,wordl+1)))
        return nexts

    def gen_feature(self,span):
        span=struct.unpack("hcch",span)
        raw=self.raw
        
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars
        c_ind=span[0]+2
        ws_current=span[1].decode()
        ws_left=span[2].decode()
        fv=[
                "ws"+ws_left+ws_current,
                "c"+uni_chars[c_ind]+ws_current,
                "r"+uni_chars[c_ind+1]+ws_current,
                'l'+uni_chars[c_ind-1]+ws_current,
                "cr"+bi_chars[c_ind]+ws_current,
                "lc"+bi_chars[c_ind-1]+ws_current,
                "rr2"+bi_chars[c_ind+1]+ws_current,
                "l2l"+bi_chars[c_ind-2]+ws_current,
            ]
        if len(span)>=4:
            w_current=raw[span[0]-span[3]:span[0]]
            fv.append("w"+w_current)
        fv=[x.encode() for x in fv]
        return fv
    

    def set_raw(self,raw):
        self.raw=raw
        self.uni_chars=list('###'+raw+'##')
        self.bi_chars=[self.uni_chars[i]+self.uni_chars[i+1]
                for i in range(len(self.uni_chars)-1)]

    def search(self,raw):
        self.set_raw(raw)
        dfabeam.set_raw([self.dfabeam,raw])
        return dfabeam.search([self.dfabeam,len(raw)+1])


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

