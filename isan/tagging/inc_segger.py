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
            'stat_fmt':"hcch",
            'init':struct.pack("hcch",0,b'|',b'|',0),
            'state_gen':None,
            'feature_gen':None,
            'beam_width':8,

            }
    def __init__(self,beam_width=8):
        self.conf=self.default_conf
        self.init=self.conf['init']
        self.beam_width=self.conf['beam_width']
        self.stat_fmt=self.conf['stat_fmt']

        self.actions={'s':{},'c':{}}
        self.link()

    def link(self):
        self.dfabeam=dfabeam.new(
                self.beam_width,
                #None,
                self.init,
                #None,
                self.keygen_for_c,
                #None,
                self.gen_feature,
                )
        dfabeam.set_action(self.dfabeam,'s',self.actions['s'])
        dfabeam.set_action(self.dfabeam,'c',self.actions['c'])
        self.stat_fmt=struct.Struct(self.conf['stat_fmt'])


    def unlink(self):
        self.stat_fmt=None

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
        stat=self.stat_fmt.unpack(stat)
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
            stat=self.stat_fmt.pack(*stat)
            dfabeam.update_action([self.dfabeam,stat,action,delta,step])
   
    def keygen_for_c(self,stat):
        ind,last,_,wordl=self.stat_fmt.unpack(stat)
        return [('s',self.stat_fmt.pack(ind+1,b's',last,1)),
            ('c',self.stat_fmt.pack(ind+1,b'c',last,wordl+1))]

    def gen_feature(self,span):
        span=self.stat_fmt.unpack(span)
        raw=self.raw
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars
        

        #fmt1=struct.Struct("c3sc")

        c_ind=span[0]+2
        ws_current=span[1]
        ws_left=span[2]
        w_current=raw[span[0]-span[3]:span[0]]
        #x=struct.pack("c3sc",b"1",uni_chars[c_ind],ws_current)
        fv=[ 
                #struct.pack("csc",b'0',ws_current,ws_left),
                b'0'+ws_current+ws_left,
                b"1"+uni_chars[c_ind]+ws_current,
                b"2"+uni_chars[c_ind+1]+ws_current,
                b'3'+uni_chars[c_ind-1]+ws_current,
                #fmt1.pack(b"1",uni_chars[c_ind],ws_current),
                #fmt1.pack(b"2",uni_chars[c_ind+1],ws_current),
                #fmt1.pack(b'3',uni_chars[c_ind-1],ws_current),
                
                b"a"+bi_chars[c_ind]+ws_current,
                b"b"+bi_chars[c_ind-1]+ws_current,
                b"c"+bi_chars[c_ind+1]+ws_current,
                b"d"+bi_chars[c_ind-2]+ws_current,
                b"w"+w_current.encode(),
                ]
        return fv
    

    def set_raw(self,raw):
        self.raw=raw
        self.uni_chars=list(x.encode() for x in '###'+raw+'##')
        self.bi_chars=[self.uni_chars[i]+self.uni_chars[i+1]
                for i in range(len(self.uni_chars)-1)]

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

