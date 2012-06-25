import collections
import pickle
import sys
import isan.tagging.cws_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
"""
一个增量搜索模式的中文分词模块
"""

class Default_Features :
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
        self.uni_chars=list('###'+raw+'##')
        self.bi_chars=[(self.uni_chars[i],self.uni_chars[i+1]) 
                for i in range(len(self.uni_chars)-1)]
    def __call__(self,span):
        raw=self.raw
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars
        c_ind=span[0]+2
        ws_current=span[1]
        ws_left=span[2]
        fv=[
                ("ws",ws_left,ws_current),
                ("c",uni_chars[c_ind],ws_current),
                ("r",uni_chars[c_ind+1],ws_current),
                ('l',uni_chars[c_ind-1],ws_current),
                ("cr",bi_chars[c_ind],ws_current),
                ("lc",bi_chars[c_ind-1],ws_current),
                ("rr2",bi_chars[c_ind+1],ws_current),
                ("l2l",bi_chars[c_ind-2],ws_current),
            ]
        if len(span)>=4:
            w_current=raw[span[0]-span[3]:span[0]]
            fv.append(("w",w_current))
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
    @staticmethod
    def constituents_to_constraints(length,constituents):
        if not constituents: return None
        spans=[[0,length+1] for i in range(length+1)]
        for left,right in constituents:
            for i in range(left+1,right):
                if left>spans[i][0]:spans[i][0]=left
                if right<spans[i][1]:spans[i][1]=right
        #print(spans)
        return spans

    def __init__(self):
        self['s']=perceptrons.Features()#特征
        self['c']=perceptrons.Features()#特征
    def set_constraints(self,constraints=None,candidates=None):
        self.candidates=candidates
        self.constraints=constraints

    def average(self,step):
        for v in self.values():
            v.average(step)
    def is_violated(self,rst_actions,candidates,constituents):
        if candidates:
            if any(a not in b for a,b in zip(rst_actions,candidates)):
                return True
        if constituents:
            constraints=self.constituents_to_constraints(len(rst_actions)-1,constituents)
            left=None
            for right,a in enumerate(rst_actions):
                if a=='s':
                    if left!=None:
                        if constraints[left][1]<right or constraints[right][0]>left:
                            return True
                        pass
                    left=right
        return False
        
class Segmentation_Stats(perceptrons.Base_Stats):
    def __init__(self,actions,features):
        self.actions=actions
        self.features=features
        #初始状态 (解析位置，上一个位置结果，上上个位置结果，当前词长)
        self.init=(0,'|','|',0)
        self.candidates=None
        self.constraints=None
    def gen_next_stats(self,stat):
        """
        由现有状态产生合法新状态
        """
        ind,last,last2,wordl=stat
        genned=False
        if self.candidates:
            if 's' in self.candidates[ind]:
                if self.constraints:
                    left=ind-wordl
                    right=ind
                    if not (self.constraints[left][1]<right 
                            or self.constraints[right][0]>left):
                        yield 's',(ind+1,'s',last,1)
                        genned=True
                else:
                    yield 's',(ind+1,'s',last,1)
                    genned=True
            if 'c' in self.candidates[ind]:    
                yield 'c',(ind+1,'c',last,wordl+1)
                genned=True
                
        else:
            if self.constraints:
                left=ind-wordl
                right=ind
                if not (self.constraints[left][1]<right or self.constraints[right][0]>left):
                    yield 's',(ind+1,'s',last,1)
                    genned=True
            else:
                yield 's',(ind+1,'s',last,1)
                genned=True
            yield 'c',(ind+1,'c',last,wordl+1)
            genned=True
        if not genned:
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



class Segmentation_Space(perceptrons.Base_Space):
    """
    线性搜索
    value = [alphas,betas]
    alpha = [score, delta, action, link]
    """
    def debug(self):
        """
        used to generate lattice
        """
        self.searcher.backward()
        sequence=self.searcher.sequence
        for i,d in enumerate(sequence):
            #print(i,"===")
            for stat,alpha_beta in d.items():
                if alpha_beta[1]:
                    for beta,db,action,n_stat in alpha_beta[1]:
                        if beta==None:continue
                        delta=alpha_beta[0][0][0]+beta-self.searcher.best_score
                        if action=='s':
                            pass
    
    def __init__(self,beam_width=8):
        super(Segmentation_Space,self).__init__(beam_width)
        self.init_data={'alphas':[(0,None,None,None)],'betas':[]}
        self.features=Default_Features()
        self.actions=Segmentation_Actions()
        self.stats=Segmentation_Stats(self.actions,self.features)

    def search(self,raw,candidates=None,constituents=None):
        self.raw=raw
        self.features.set_raw(raw)

        self.sequence=[{}for x in range(len(raw)+2)]
        
        constraints=self.actions.constituents_to_constraints(len(raw),constituents)
        self.actions.set_constraints(candidates,constraints)
        
        self.forward()
        res=self.make_result()
        return res

    def gen_next(self,ind,stat):
        """
        根据第ind步的状态stat，产生新状态，并计算data
        """
        fv=self.features(stat)
        alpha_beta=self.sequence[ind][stat]
        beam=self.sequence[ind+1]
        for action,key in self.stats.gen_next_stats(stat):
            if key not in beam:
                beam[key]={'alphas':[],'betas':[]}
            value=self.actions[action](fv)
            beam[key]['alphas'].append((alpha_beta['alphas'][0][0]+value,value,action,stat))

    def make_result(self):
        """
        由状态及data计算actions
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
    def __init__(self,model_file,schema=None,**conf):
        """
        初始化
        schema： 如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        super(Model,self).__init__(model_file,schema)
        self.codec=tagging_codec
        self.Eval=tagging_eval.TaggingEval
        self.step=0

    #        
    #def _learn_sentences(self,raw,y=None,candidates=None,constituents=None):
    #    """
    #    学习，根据生句子和标准分词结果
    #    """
    #    if y:#传统训练样本
    #        self.step+=1#学习步数加一
    #        std_actions=self.actions.result_to_actions(y)#得到标准动作
    #        rst_actions=self.schema.search(raw)#得到解码后动作
    #        hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
    #        if y!=hat_y:#如果动作不一致，则更新
    #            self.stats.update(raw,std_actions,rst_actions,self.step)
    #    else :#广义训练样本
    #        rst_actions=self.schema.search(raw)#得到解码后动作
    #        hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
    #        if self.schema.is_violated(rst_actions,candidates,constituents):
    #            self.step+=1#学习步数加一
    #            std_actions=self.schema.search(raw,candidates=candidates,constituents=constituents)#得到解码后动作
    #            y=self.actions.actions_to_result(std_actions,raw)#得到解码后结果
    #            #print(y,hat_y)
    #            self.stats.update(raw,std_actions,rst_actions,self.step)
    #        else:
    #            y=hat_y
    #        #print(y)
    #    return y,hat_y
    #def trains(self,training_file,iteration=5):
    #    """
    #    训练
    #    """
    #    for it in range(iteration):#迭代整个语料库
    #        eval=self.Eval()#测试用的对象
    #        if type(training_file)==str:training_file=[training_file]

    #        for t_file in training_file:
    #            for line in open(t_file):#迭代每个句子
    #                y=self.codec.decode(line.strip())
    #                if type(y)==tuple :
    #                    constituents=y[2] if len(y)>2 else None
    #                    y,hat_y=self._learn_sentence(y[0],candidates=y[1],constituents=constituents)
    #                else:
    #                    raw=''.join(y)
    #                    y,hat_y=self._learn_sentence(raw,y)
    #                eval(y,hat_y)#学习它
    #        eval.print_result()#打印评测结果
