import collections
import pickle
import sys
import isan.tagging.cws_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
import isan.tagging.dfabeam as dfabeam
"""
一个增量搜索模式的中文分词模块
"""

class Default_Features_s :
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        #cwsfeature.set_raw(raw)
        #return
        self.raw=raw
        self.uni_chars=list('###'+raw+'##')
        self.bi_chars=[self.uni_chars[i]+self.uni_chars[i+1]
                for i in range(len(self.uni_chars)-1)]

    def __call__(self,span):
        #return cwsfeature.get_features(span)
        raw=self.raw
        
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars
        c_ind=span[0]+2
        ws_current=span[1]
        ws_left=span[2]
        
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


        
class Segmentation_Actions(dict):
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

    def __init__(self,beam):

        self.dfabeam=beam
        dfabeam.set_action([self.dfabeam,'s'])
        dfabeam.set_action([self.dfabeam,'c'])


    def average(self,step):
        pass
        
class Segmentation_Stats(perceptrons.Base_Stats):
    def __init__(self):
        #初始状态 (解析位置，上一个位置结果，上上个位置结果，当前词长)
        self.init=(0,'|','|',0)

    def _actions_to_stats(self,actions):
        stat=self.init
        for action in actions:
            yield stat
            ind,last,_,wordl=stat
            if action=='s':
                stat=(ind+1,'s',last,1)
            else:
                stat=(ind+1,'c',last,wordl+1)
        yield stat


class Segmentation_Space:
    """
    线性搜索
    value = [alphas,betas]
    alpha = [score, delta, action, link]
    """
   
    def keygen_for_c(self,stat,nexts):
        ind,last,_,wordl=stat
        nexts.append(((ind+1,'s',last,1),'s'))
        nexts.append(((ind+1,'c',last,wordl+1),'c'))
        return None
        #nexts.extends(self.stats.gen_next_stats(stat))
        for action,key in self.stats.gen_next_stats(stat):
            nexts.append((key,action))
        return None

    def __init__(self,beam_width=8):
        self.stats=Segmentation_Stats()
        self.dfabeam=dfabeam.new([
                self.stats.init,
                self.keygen_for_c,
                beam_width])
        self.actions=Segmentation_Actions(self.dfabeam)
        self.stats.dfabeam=self.dfabeam


    def __del__(self):
        self.delete(self.dfabeam)

    def search(self,raw):
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

