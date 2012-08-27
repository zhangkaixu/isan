import collections
import pickle
import sys
import isan.tagging.cws_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
import isan.tagging.cwsfeature as cwsfeature
import isan.tagging.dfabeam as dfabeam
"""
一个增量搜索模式的中文分词模块
"""

class Default_Features_inC :
    def set_raw(self,raw):
        cwsfeature.set_raw(raw)
    def __call__(self,span):
        return cwsfeature.get_features(span)

class Default_Features :
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

    def __init__(self):
        self['s']=perceptrons.Weights()#特征
        self['c']=perceptrons.Weights()#特征

    def average(self,step):
        for v in self.values():
            v.average(step)
    def new_action(self,action):
        self[action]=perceptrons.Weights()
        
class Segmentation_Stats(perceptrons.Base_Stats):
    def __init__(self,actions,features):
        self.actions=actions
        self.features=features
        #初始状态 (解析位置，上一个位置结果，上上个位置结果，当前词长)
        self.init=(0,'|','|',0)
    def gen_next_stats(self,stat,set_Y=None):
        """
        由现有状态产生合法新状态
        """
        ind,last,_,wordl=stat
        yield 's',(ind+1,'s',last,1)
        yield 'c',(ind+1,'c',last,wordl+1)

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


class Segmentation_Space(perceptrons.Base_Decoder):
    """
    线性搜索
    value = [alphas,betas]
    alpha = [score, delta, action, link]
    """
    #def debug(self):
    #    """
    #    used to generate lattice
    #    """
    #    self.searcher.backward()
    #    sequence=self.searcher.sequence
    #    for i,d in enumerate(sequence):
    #        for stat,alpha_beta in d.items():
    #            if alpha_beta[1]:
    #                for beta,db,action,n_stat in alpha_beta[1]:
    #                    if beta==None:continue
    #                    delta=alpha_beta[0][0][0]+beta-self.searcher.best_score
    #                    if action=='s':
    #                        pass
    
    def keygen_for_c(self,stat,nexts):
        fv=self.features(stat)#得到当前状态的特征向量
        #nexts=[]
        for action,key in self.stats.gen_next_stats(stat,self.set_Y):
            nexts.append((key,action,self.actions[action](fv)))
        return
        #f2=[x for x in fv]
        #fv+=f2+f2
        #print(nexts)
        #input()
        #return nexts
    def __init__(self,beam_width=8):
        super(Segmentation_Space,self).__init__(beam_width)
        self.init_data={'alphas':[(0,None,None,None)],'betas':[]}
        self.features=Default_Features()
        self.actions=Segmentation_Actions()
        self.stats=Segmentation_Stats(self.actions,self.features)
        #dfabeam.set_init([self.stats.init,self.keygen_for_c])
        self.dfabeam=dfabeam.new([self.stats.init,self.keygen_for_c,8])


    def __del__(self):
        self.delete(self.dfabeam)
        pass

    def search(self,raw,set_Y=None):
        self.raw=raw
        self.set_Y=set_Y
        self.features.set_raw(raw)
        dfabeam.set_raw([self.dfabeam,raw])
        re=dfabeam.search([self.dfabeam,len(raw)+1])
        self.sequence=[{}for x in range(len(raw)+2)]
        return re
        self.sequence=[{}for x in range(len(raw)+2)]
        self.forward()
        res=self.make_result()
        #print(res)
        #print(re)
        return res

    def gen_next(self,ind,stat):
        """
        根据第ind步的状态stat，产生新状态，并计算data
        """
        fv=self.features(stat)#得到当前状态的特征向量
        alpha_beta=self.sequence[ind][stat]
        beam=self.sequence[ind+1]
        for action,key in self.stats.gen_next_stats(stat,self.set_Y):
            if key not in beam:
                beam[key]={'alphas':[],'betas':[]}
            value=self.actions[action](fv)
            beam[key]['alphas'].append((alpha_beta['alphas'][0][0]+value,value,action,stat))

    def make_result(self):
        """
        由alphas中间的记录计算actions
        """
        sequence=self.sequence
        result=[]
        item=sequence[-1][self.thrink(len(sequence)-1)[0]]['alphas'][0]
        self.best_score=item[0]
        ind=len(sequence)-2
        while True :
            if item[3]==None: break
            result.append(item[2])
            item=sequence[ind][item[3]]['alphas'][0]
            ind-=1
        result.reverse()
        return result


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

