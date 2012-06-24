import collections
import pickle
import sys
import isan.tagging.cws_codec as tagging_codec
import isan.tagging.eval as tagging_eval
import isan.common.perceptrons as perceptrons
"""
一个增量搜索模式的中文分词模块
"""

class Defalt_Features:
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


class Searcher:
    def __init__(self,beam_width=8):
        self.sequence=[]
        self.beam_width=beam_width
    def thrink(self,ind):
        #sort alphas
        for k,v in self.sequence[ind].items():
            #alphas=v['alphas']
            #max_ind=max(enumerate(v['alphas']),key=lambda x:x[1])[0]
            #alphas[0],alphas[max_ind]=alphas[max_ind],alphas[0]
            v['alphas'].sort(reverse=True)
        #thrink beam
        beam=sorted(list(self.sequence[ind].items()),key=lambda x:x[1]['alphas'][0],reverse=True)
        beam=beam[:min(len(beam),self.beam_width)]
        return [stat for stat,_ in beam]
    def forward(self,sequence,model):
        """
        线性搜索
        value = [alphas,betas]
        alpha = [score, delta, action, link]
        """
        self.sequence=sequence
        sequence[0][model.init]=dict(model.init_data)#初始化第一个状态
        for ind in range(len(model.raw)+1):
            for stat in self.thrink(ind):
                model.gen_next(ind,stat)
    def backward(self):
        """
        使用beta算法计算后向分数
        """
        sequence=self.sequence
        ind=len(sequence)-1
        for stat,alpha_beta in sequence[ind].items():#初始化最后一项的分数
            alpha_beta[1].append((0,None,None,None))
        while ind>0:
            for stat,alpha_beta in sequence[ind].items():
                alphas=alpha_beta[0]
                if not alpha_beta[1]: continue
                beta=alpha_beta[1][0][0]
                for score,delta,action,pre_stat in alphas:
                    sequence[ind-1][pre_stat][1].append((beta+delta,delta,action,stat))
            #排序
            for _,alpha_beta in sequence[ind-1].items():
                alpha_beta[1].sort(reverse=True)
            ind-=1
        
        
class Defalt_Actions:
    def debug(self):
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
        pass
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

    
    def __init__(self,
                features=Defalt_Features,beam_width=8):
        self.sep_weights=perceptrons.Features()#特征
        self.com_weights=perceptrons.Features()#特征
        self.weights={'s':self.sep_weights,
                'c':self.com_weights}
        self.features=features()
        self.searcher=Searcher(beam_width)
        #初始状态 (解析位置，上一个位置结果，上上个位置结果，当前词长)
        self.init=(0,'|','|',0)
        self.init_data={'alphas':[(0,None,None,None)],'betas':[]}
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

    def gen_next(self,ind,stat):
        """
        产生新状态，并计算data
        """
        fv=self.features(stat)
        alpha_beta=self.sequence[ind][stat]
        beam=self.sequence[ind+1]
        for action,key in self.gen_next_stats(stat):
            if key not in beam:
                beam[key]={'alphas':[],'betas':[]}
            #value=self.sep_weights(fv) if action=='s' else self.com_weights(fv)
            value=self.weights[action](fv)
            beam[key]['alphas'].append((alpha_beta['alphas'][0][0]+value,value,action,stat))

    def make_result(self):
        """
        由状态及data计算actions
        """
        sequence=self.sequence
        result=[]
        item=sequence[-1][self.searcher.thrink(len(sequence)-1)[0]]['alphas'][0]
        self.best_score=item[0]
        ind=len(sequence)-2
        while True :
            if item[3]==None: break
            result.append(item[2])
            item=sequence[ind][item[3]]['alphas'][0]
            ind-=1
        result.reverse()
        return result
    def search(self,raw,candidates=None,constituents=None):
        self.raw=raw
        self.candidates=candidates
        self.constraints=self.constituents_to_constraints(len(raw),constituents)
        self.features.set_raw(raw)
        self.sequence=[{}for x in range(len(raw)+2)]
        self.searcher.forward(self.sequence,self)
        res=self.make_result()
        return res
    def update(self,x,std_actions,rst_actions,step):
        self._update_actions(rst_actions,-1,step)
        self._update_actions(std_actions,1,step)

    def is_violated(self,rst_actions,candidates,constituents):
        if candidates:
            if any(a not in b for a,b in zip(rst_actions,candidates)):
                return True
        if constituents:
            constraints=self.constituents_to_constraints(len(rst_actions)-1,constituents)
            #print(constraints)
            left=None
            for right,a in enumerate(rst_actions):
                if a=='s':
                    #print(left,right) 
                    if left!=None:
                        if constraints[left][1]<right or constraints[right][0]>left:
                            #print('violated')
                            return True
                        pass
                    left=right
        return False
    def average(self,step):
        for v in self.weights.values():
            v.average(step)
    ### 私有函数 
    def _update_actions(self,actions,delta,step):
        stat=self.init
        for action in actions:
            fv=self.features(stat)
            ind,last,last2,wordl=stat
            self.weights[action].updates(fv,delta,step)
            if action=='s':
                stat=(ind+1,'s',last,1)
            else:
                stat=(ind+1,'c',last,wordl+1)

class Model:
    """
    模型
    """
    def __init__(self,model_file,actions=None):
        """
        初始化
        actions： 如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        if actions==None:
            file=open(model_file,"rb")
            self.actions=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.actions=actions
            self.step=0
            
    def __call__(self,raw):
        """
        解码，读入生句子，返回词的数组
        """
        rst_actions=self.actions.search(raw)
        hat_y=self.actions.actions_to_result(rst_actions,raw)
        return hat_y
    def _learn_sentence(self,raw,y=None,candidates=None,constituents=None):
        """
        学习，根据生句子和标准分词结果
        """
        
        if y:#传统训练样本
            self.step+=1#学习步数加一
            std_actions=self.actions.result_to_actions(y)#得到标准动作
            rst_actions=self.actions.search(raw)#得到解码后动作
            hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
            if y!=hat_y:#如果动作不一致，则更新
                self.actions.update(raw,std_actions,rst_actions,self.step)
        else :#广义训练样本
            rst_actions=self.actions.search(raw)#得到解码后动作
            hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
            if self.actions.is_violated(rst_actions,candidates,constituents):
                self.step+=1#学习步数加一
                std_actions=self.actions.search(raw,candidates=candidates,constituents=constituents)#得到解码后动作
                y=self.actions.actions_to_result(std_actions,raw)#得到解码后结果
                #print(y,hat_y)
                self.actions.update(raw,std_actions,rst_actions,self.step)
            else:
                y=hat_y
            #print(y)
        return y,hat_y
    def save(self):
        """
        保存模型
        """
        self.actions.average(self.step)
        file=open(self.model_file,'wb')
        pickle.dump(self.actions,file)
        file.close()
    def train(self,training_file,iteration=5):
        """
        训练
        """
        for it in range(iteration):#迭代整个语料库
            eval=tagging_eval.TaggingEval()#测试用的对象
            if type(training_file)==str:training_file=[training_file]

            for t_file in training_file:
                for line in open(t_file):#迭代每个句子
                    y=tagging_codec.decode(line.strip())
                    if type(y)==tuple :
                        constituents=y[2] if len(y)>2 else None
                        y,hat_y=self._learn_sentence(y[0],candidates=y[1],constituents=constituents)
                    else:
                        raw=''.join(y)
                        y,hat_y=self._learn_sentence(raw,y)
                    eval(y,hat_y)#学习它
            eval.print_result()#打印评测结果
    def test(self,test_file):
        """
        测试
        """
        eval=tagging_eval.TaggingEval()
        for line in open(test_file):
            y=tagging_codec.decode(line.strip())
            raw=''.join(y)
            hat_y=self(raw)
            eval(y,hat_y)
        eval.print_result()
