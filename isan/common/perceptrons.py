"""
ZHANG Kaixu


"""
import logging
import sys
import pickle
import collections
import random
import gzip


class Model(object):
    """平均感知器模型


    """
    name="平均感知器" #: 模型的名字

    def __init__(self,model_file,task=None,Searcher=None,beam_width=8,**conf):
        """
        初始化
        如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        logging.basicConfig(level=logging.DEBUG)
        #logging.basicConfig(level=logging.INFO)
        self.logger=logging.getLogger(__name__)
        self.beam_width=beam_width#:搜索宽度
        self.conf=conf

        self.task=task
        if model_file!=None:
            file=gzip.open(model_file,"rb")
            self.task.weights=pickle.load(file)
            file.close()
        else:
            #self.model_file=model_file
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
    def save(self,model_file=None):
        """
        保存模型
        """

        if model_file==None : model_file=self.model_file
        if model_file==None : return

        self.searcher.average_weights(self.step)
        self.task.weights=self.searcher.export_weights()
        #file=open(model_file,'wb')
        file=gzip.open(model_file,'wb')
        pickle.dump(self.task.weights,file)
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

        #self.logger.debug('get training example')
        #self.logger.debug("raw: %s"%raw)
        #self.logger.debug("y: %s"%y)
        #self.logger.debug("Y_a: %s"%Y_a)


        #学习步数加一
        self.step+=1

        #set oracle, get standard actions
        if hasattr(self.task,'set_oracle'):
            std_moves=self.task.set_oracle(raw,y)

        #self.logger.debug(std_moves)

        #get result actions
        self.searcher.set_step(self.step)
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

        
    def train(self,training_file,iteration=5,dev_file=None,keep_data=True):
        """
        训练
        """
        if type(training_file)==str:training_file=[training_file]
        #random.seed(123)

        if keep_data :
            training_data=[]
            for t_file in training_file :
                for line in open(t_file):#迭代每个句子
                    rtn=self.task.codec.decode(line.strip())#得到标准输出
                    if not rtn:continue
                    training_data.append(rtn)
            random.shuffle(training_data)

        def gen_data():
            if keep_data :
                perc=0
                print(perc,end='%\r')
                #random.shuffle(training_data)
                for i,e in enumerate(training_data) :
                    p=int(i*100/len(training_data))
                    if p != perc :
                        print("%i"%(p),end='%\r',file=sys.stderr)
                        perc=p
                    yield e
            else :
                for t_file in training_file:
                    for line in open(t_file):#迭代每个句子
                        rtn=self.task.codec.decode(line.strip())#得到标准输出
                        if not rtn:continue
                        yield rtn

        for it in range(iteration):#迭代整个语料库
            print("训练集第 \033[33;01m%i\033[1;m 次迭代"%(it+1),file=sys.stderr)
            eval=self.task.Eval()#: 测试用的对象

            for rtn in gen_data():
                y,hat_y=self._learn_sentence(rtn)#根据（输入，输出）学习参数，顺便得到解码结果
                eval(y,hat_y)#根据解码结果和标准输出，评价效果
            eval.print_result()#打印评测结果

            if hasattr(self.task,'report'):
                self.task.report()
            
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
        #print(arg)
        
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
                #print('yb',Y_b)
                std_moves=self.search(raw,Y_b)
            self.update(std_moves,rst_moves)
        hat_y=self.task.moves_to_result(rst_moves,raw)#得到解码后结果
        return y,hat_y
