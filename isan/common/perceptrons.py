#!/usr/bin/python3
import pickle
import collections
class Weights(dict):
    """
    感知器特征的权重
    """
    def __init__(self):
        self.acc=collections.defaultdict(int)
    def update(self,feature,delta=0,step=0):
        self.setdefault(feature,0)
        self[feature]+=delta
        self.acc[feature]+=step*delta
    def __call__(self,fv):
        #return 0
        return sum(self.get(x,0)for x in fv)
        #return sum(map(lambda x:self.get(x,0),fv))
    def updates(self,features,delta=0,step=0):
        for feature in features:
            self.setdefault(feature,0)
            self[feature]+=delta
            self.acc[feature]+=step*delta
    def average(self,step):
        for k in self.acc:
            self[k]=(self[k]-self.acc[k]/step)
            if self[k]==0:del self[k]
        del self.acc

class Base_Decoder(object):
    """
    解码

    self.sequence: 动作序列的beam
    
    需要实现：
    self.gen_next(ind,stat) # 第ind个动作，当前状态为stat时候，产生后续状态

    """
    def __init__(self,beam_width):
        self.beam_width=beam_width#搜索柱宽度
    def thrink(self,ind):
        #找到最好的alphas
        for k,v in self.sequence[ind].items():
            #这里使用排序比使用max还快，但保留max的代码
            #alphas=v['alphas']
            #max_ind=max(enumerate(v['alphas']),key=lambda x:x[1])[0]
            #alphas[0],alphas[max_ind]=alphas[max_ind],alphas[0]
            
            v['alphas'].sort(reverse=True,key=lambda x:x[0])
        #构造beam
        beam=sorted(list(self.sequence[ind].items()),key=lambda x:x[1]['alphas'][0][0],reverse=True)
        #print(len(beam))
        beam=beam[:min(len(beam),self.beam_width)]
        #print(len(beam))
        return [stat for stat,_ in beam]
    def forward(self):
        #前向搜索
        self.sequence[0][self.stats.init]=dict(self.init_data)#初始化第一个状态
        for ind in range(len(self.raw)+1):
            for stat in self.thrink(ind):
                self.gen_next(ind,stat)
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

class Base_Stats(object):
    """
    需要实现
    self.init 初始状态
    self.gen_next_stats
    self._actions_to_stats
    """
    def update(self,x,std_actions,rst_actions,step,sequence=None):
        #print("begin")
        length=self._update_actions(std_actions,1,step,sequence)
        #print(len(sequence),length)
        length=self._update_actions(rst_actions,-1,step,sequence[:length])
        #print(length)
        #print("end")
    ### 私有函数 
    def _update_actions(self,actions,delta,step,sequence):
        length=0
        #print(len(actions),len(sequence))
        for stat,action,beam in zip(self._actions_to_stats(actions),actions,sequence[:]):
            fv=self.features(stat)
            if action not in self.actions:
                #print(action)
                self.actions.new_action(action)
            self.actions[action].updates(fv,delta,step)
            length+=1
            if stat not in beam:
                #print('early update',length)
                #return length
                pass
        return length

class Base_Model(object):
    def __init__(self,model_file,schema=None,**conf):
        """
        初始化
        schema： 如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        self.conf=conf
        if schema==None:
            file=open(model_file,"rb")
            self.schema=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.schema=schema
        self.actions=self.schema.actions
        self.stats=self.schema.stats
        self.step=0

    def test(self,test_file):
        """
        测试
        """
        eval=self.Eval()
        for line in open(test_file):
            y=self.codec.decode(line.strip())
            raw=self.codec.to_raw(y)
            hat_y=self(raw)
            eval(y,hat_y)
        eval.print_result()
    def save(self):
        """
        保存模型
        """
        self.actions.average(self.step)
        file=open(self.model_file,'wb')
        pickle.dump(self.schema,file)
        file.close()
    def __call__(self,raw):
        """
        解码，读入生句子，返回词的数组
        """
        rst_actions=self.schema.search(raw)
        hat_y=self.actions.actions_to_result(rst_actions,raw)
        return hat_y
    def _learn_sentence(self,raw,y):
        """
        学习，根据生句子和标准分词结果
        """
        self.step+=1#学习步数加一
        std_actions=self.actions.result_to_actions(y)#得到标准动作
        rst_actions=self.schema.search(raw)#得到解码后动作
        hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
        """这里需要考虑如何引入都说好的early update！"""
        if y!=hat_y:#如果动作不一致，则更新
            self.stats.update(raw,std_actions,rst_actions,self.step,self.schema.sequence)
        return y,hat_y
        
    def train(self,training_file,iteration=5):
        """
        训练
        """
        for it in range(iteration):#迭代整个语料库
            eval=self.Eval()#测试用的对象
            if type(training_file)==str:training_file=[training_file]
            for t_file in training_file:
                for line in open(t_file):#迭代每个句子
                    y=self.codec.decode(line.strip())#得到标准输出
                    raw=self.codec.to_raw(y)#得到标准输入
                    y,hat_y=self._learn_sentence(raw,y)#根据（输入，输出）学习参数，顺便得到解码结果
                    eval(y,hat_y)#根据解码结果和标准输出，评价效果
            eval.print_result()#打印评测结果
