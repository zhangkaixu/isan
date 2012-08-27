#!/usr/bin/python3
import pickle
import collections
import isan.tagging.dfabeam as dfabeam


class Base_Stats(object):
    """
    需要实现
    self.init 初始状态
    self.gen_next_stats
    self._actions_to_stats
    """
    def update(self,x,std_actions,rst_actions,step):
        self._update_actions(std_actions,1,step)
        self._update_actions(rst_actions,-1,step)
    ### 私有函数 
    def _update_actions(self,actions,delta,step):
        for stat,action in zip(self._actions_to_stats(actions),actions,):
            dfabeam.update_action([self.dfabeam,stat,action,delta,step])

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
            raw,y,set_Y=self.codec.decode(line.strip())
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
    def _learn_sentence(self,raw,y,set_Y=None):
        """
        学习，根据生句子和标准分词结果
        """
        self.step+=1#学习步数加一
        if y:
            std_actions=self.actions.result_to_actions(y)#得到标准动作
        else:
            std_actions=self.schema.search(raw,set_Y)
        rst_actions=self.schema.search(raw)#得到解码后动作
        hat_y=self.actions.actions_to_result(rst_actions,raw)#得到解码后结果
        if y!=hat_y:#如果动作不一致，则更新
            self.stats.update(raw,std_actions,rst_actions,self.step)
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
                    rtn=self.codec.decode(line.strip())#得到标准输出
                    if not rtn:continue
                    raw,y,set_Y=rtn
                    #raw=self.codec.to_raw(y)#得到标准输入
                    y,hat_y=self._learn_sentence(raw,y,set_Y)#根据（输入，输出）学习参数，顺便得到解码结果
                    eval(y,hat_y)#根据解码结果和标准输出，评价效果
            eval.print_result()#打印评测结果
