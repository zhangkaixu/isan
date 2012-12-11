#!/usr/bin/python3
"""
ZHANG Kaixu


平均感知器算法的伪代码

.. code-block:: python
    :linenos:
    
    for x,y in training_data:
        z=argmax(f(x,z)*alpha))#: 向量乘法
        if z!=y:
            alpha=alpha+f(x,y)-f(x,z)

会生成一个 :py:class:`Task.Eval` 对象，用于评测


1. 读入一行数据，使用 :py:meth:`Task.codec.decode` 解码。 使用 :py:meth:`Task.set_oracle` 来设置标准答案，并且得到标准的动作。
2. 开始寻找正确答案， :py:meth:`Task.set_raw` 设置输入， 调用搜索算法得到输出。 这里还可能用到 :py:meth:`Task.early_stop` 来判断是否需要提前结束搜索。
3. 用 :py:meth:`Task.check` 判断是否是正确输出
4. 使用 :py:meth:`Task.update_moves` 来判断哪些地方需要更新权重。 
5. :py:meth:`Task.remove_oracle` 去掉标准答案。 最后用 :py:meth:`Task.moves_to_result` 得到输出结果，用于评测


"""
import sys
import pickle
import collections



class Task:
    """
    task

    """

    """weights"""
    weights=None

    class Eval:
        """
        用于评测"""


    def set_raw(self,raw,Y):
        """
        设置输入
        """
        pass
    def set_oracle(self,raw,y,Y_b=None):
        """
        设置标准输出。

        y 不一定需要给出，可以给出Y_b

        :param raw: raw sentence
        :param y: gold standard output
        :param Y_b: a set (or other data structure) containing y
        """
        pass
    def check(self,std_moves,rst_moves):
        """
        
        :param std_moves: 标准运动
        :param rst_moves: 解码得到的运动
        :return: 1 表示正确，不需要更新权重， 0 表示需要更新权重。

        """
        pass
    def remove_oracle(self):
        """
        need to be removed
        """
        pass
    def update_moves(self,std_moves,rst_moves):
        """

        :param std_moves: 标准运动
        :param rst_moves: 解码得到的运动
        :return: 三元组 ``(state,action,delta)`` 的序列

        """
    def moves_to_result(self,rst_moves,raw):
        """
        from move to result
        """


    class codec:
        """ codec """
        @staticmethod
        def decode(line):
            """

            :rtype: :py:func:`dict` ``{'raw': raw, 'y': y, 'Y_a':ya}``
            """

    def shift(self,last_ind,stat):
        """ 处理 shift 动作

        :param integer step: 当前步骤
        :param bytes state: 当前状态
        :return: list of tuples `[(action, next_step, next_state) , ...]`

        """


class Model(object):
    """平均感知器模型


    """
    name="平均感知器" #: 模型的名字

    def __init__(self,model_file,task=None,Searcher=None,beam_width=8,**conf):
        """
        初始化
        如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        self.beam_width=beam_width#:搜索宽度
        self.conf=conf
        if task==None:
            file=open(model_file,"rb")
            self.task=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.task=task
            self.task.weights={}
        if hasattr(self.task,'init'):
            self.task.init()
        self.searcher=Searcher(self.task,beam_width)
        self.searcher.set_action(self.task.weights)
        self.step=0

    def __del__(self):
        del self.searcher
    def test(self,test_file):
        """
        测试
        """
        self.searcher.make_dat()
        eval=self.task.Eval()
        for line in open(test_file):
            arg=self.task.codec.decode(line.strip())
            raw=arg.get('raw')
            Y=arg.get('Y_a',None)
            y=arg.get('y',None)
            hat_y=self(raw,Y)
            eval(y,hat_y)
        eval.print_result()
        return eval
    
    def develop(self,dev_file):
        """
        @brief 预测开发集
        """
        self.searcher.average_weights(self.step)
        #print(self.searcher.export_weights())
        #self.searcher.set_action({b'a0~0':100})
        #print(self.searcher.export_weights())
        eval=self.task.Eval()
        for line in open(dev_file):
            arg=self.task.codec.decode(line.strip())
            if not arg:continue
            raw=arg.get('raw')
            y=arg.get('y',None)
            hat_y=self(raw)
            

            eval(y,hat_y)
        eval.print_result()
        self.searcher.un_average_weights()

        pass
    def save(self):
        """
        保存模型
        """
        self.searcher.average_weights(self.step)
        #for k,v in self.searcher.export_weights():
        #    self.task.weights.setdefault(k,{}).update(v)
        self.task.weights=self.searcher.export_weights()
        file=open(self.model_file,'wb')
        pickle.dump(self.task,file)
        file.close()

    def search(self,raw,Y=None):
        """
        搜索

        :param raw: 输入
        :param Y: 对输出的限制，可为空

        首先使用 :py:meth:`Task.set_raw` 为 :py:class:`Task` 设置输入，
        然后调用搜索算法搜索结果。

        .. code-block:: python

            def search(self,raw,Y=None):
                self.task.set_raw(raw,Y)
                self.searcher.set_raw(raw)
                return self.searcher.search()
        

        """
        self.task.set_raw(raw,Y)
        self.searcher.set_raw(raw)
        return self.searcher.search()

    def __call__(self,raw,Y=None,threshold=0):
        """
        解码，读入生句子，返回词的数组
        """
        rst_moves=self.search(raw,Y)
        hat_y=self.task.moves_to_result(rst_moves,raw)
        if threshold==0 : 
            return hat_y
        else:
            states=self.searcher.get_states()
            return self.task.gen_candidates(states,threshold)

    def _learn_sentence(self,arg):
        """
        学习，根据生句子和标准分词结果
        """
        raw=arg.get('raw')
        self.raw=raw
        y=arg.get('y',None)
        Y_a=arg.get('Y_a',None)


        #学习步数加一
        self.step+=1

        #set oracle, get standard actions
        if hasattr(self.task,'set_oracle'):
            std_moves=self.task.set_oracle(raw,y)

        #get result actions
        rst_moves=self.search(raw,Y_a)#得到解码后动作

        #update
        if not self.task.check(std_moves,rst_moves):#check
            self.update(std_moves,rst_moves)#update

        #clean oracle
        if hasattr(self.task,'remove_oracle'):
            self.task.remove_oracle()

        hat_y=self.task.moves_to_result(rst_moves,raw)#得到解码后结果
        return y,hat_y

    def update(self,std_moves,rst_moves):
        if hasattr(self.task,'update_moves'):
            for move,delta in self.task.update_moves(std_moves,rst_moves) :
                self.searcher.update_action(move,delta,self.step)
            return

        
    def train(self,training_file,iteration=5,dev_file=None):
        """

        训练
        
        根据一个Task

        循环

        首先生成一个 :py:class:`Task.Eval` 用于评测

        读入一行 line

        使用 :py:meth:`Task.codec.decode` 解码

        
        """
        for it in range(iteration):#迭代整个语料库
            print("训练集第 \033[33;01m%i\033[1;m 次迭代"%(it+1),file=sys.stderr)
            eval=self.task.Eval()#: 测试用的对象
            if type(training_file)==str:training_file=[training_file]
            for t_file in training_file:
                for line in open(t_file):#迭代每个句子
                    rtn=self.task.codec.decode(line.strip())#得到标准输出
                    if not rtn:continue
                    y,hat_y=self._learn_sentence(rtn)#根据（输入，输出）学习参数，顺便得到解码结果
                    eval(y,hat_y)#根据解码结果和标准输出，评价效果
            eval.print_result()#打印评测结果
            
            if dev_file:
                print("使用开发集 %s 评价当前模型效果"%(dev_file),file=sys.stderr)
                self.develop(dev_file)
            #input('end of one iteration')


class Model_PA(Model) :
    name="局部标注平均感知器"
    def _learn_sentence(self,arg):
        """
        学习，根据生句子和标准分词结果
        """
        raw=arg.get('raw')
        self.raw=raw
        y=arg.get('y',None)
        Y_a=arg.get('Y_a',None)
        Y_b=arg.get('Y_b',None)
        
        #学习步数加一
        self.step+=1

        #get standard actions
        if hasattr(self.task,'set_oracle'):
            std_moves=self.task.set_oracle(raw,y,Y_b)

        #get result actions
        rst_moves=self.search(raw,Y_a)#得到解码后动作

        #clean the early-update data
        if hasattr(self.task,'remove_oracle'):
            self.task.remove_oracle()

        if not self.task.is_belong(raw,rst_moves,Y_b): #不一致，则更新
            if y and not Y_b :
                std_moves=self.task.result_to_moves(y)#得到标准动作
            else :
                std_moves=self.search(raw,Y_b)
            self.update(std_moves,rst_moves)
        hat_y=self.task.moves_to_result(rst_moves,raw)#得到解码后结果
        return y,hat_y
