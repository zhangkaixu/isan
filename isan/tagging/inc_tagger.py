import collections
import pickle
import sys
import isan.tagging.inc_segger as segger
import isan.tagging.tagging_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
"""
一个增量搜索模式的中文分词模块
"""


        
class Segmentation_Actions(segger.Segmentation_Actions):
    @staticmethod
    def actions_to_result(actions,raw):
        sen=[]
        cache=''
        #print(actions,raw)
        for c,a in zip(raw,actions[1:]):
            cache+=c
            a,tag=a
            if a=='s':
                sen.append((cache,tag))
                cache=''
        if cache:
            sen.append((cache,tag))
        return sen
    @staticmethod
    def result_to_actions(y):
        #print(y)
        actions=[('s','$')]
        for w,t in y:
            for i in range(len(w)-1):
                actions.append(('c',t))
            actions.append(('s',t))
        return actions

    def __init__(self):
        self[('s','$')]=perceptrons.Weights()#特征

        
class Segmentation_Stats(segger.Segmentation_Stats):
    def gen_next_stats(self,stat):
        """
        由现有状态产生合法新状态
        """
        ind,last,_,wordl=stat
        last_sc=last[0]
        last_tag=last[1:]
        for act in self.actions:
            sc,tag=act
            if last_sc=='c' and last_tag!=tag: continue
            yield act,(ind+1,sc+tag,last,1 if sc=='s' else wordl+1)

    def _actions_to_stats(self,actions):
        stat=self.init
        for action in actions:
            action,tag=action
            yield stat
            ind,last,_,wordl=stat
            stat=(ind+1,action+tag,last,1 if action=='s' else wordl+1)
        yield stat



class Segmentation_Space(segger.Segmentation_Space):
    def __init__(self,beam_width=8):
        super(Segmentation_Space,self).__init__(beam_width)
        self.init_data={'alphas':[(0,None,None,None)],'betas':[]}
        self.features=segger.Default_Features()
        self.actions=Segmentation_Actions()
        self.stats=Segmentation_Stats(self.actions,self.features)

    
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

