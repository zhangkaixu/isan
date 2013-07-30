"""
ZHANG Kaixu
"""
import logging
import sys
import pickle
import random
import gzip
from isan.common.weights import Weights

class Model(object):
    """平均感知器模型 """
    name="平均感知器" #: 模型的名字

    def __init__(self,model_file,Task=None,Searcher=None,beam_width=8,logger=None,cmd_args={},**conf):
        """
        初始化
        如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        if logger==None :
            logger=logging.getLogger(__name__)
            console=logging.StreamHandler()
            console.setLevel(logging.INFO)
            logger.addHandler(console)
            logger.setLevel(logging.INFO)
        self.result_logger=logger

        self.beam_width=beam_width#:搜索宽度
        self.conf=conf

        if model_file!=None:
            file=gzip.open(model_file,"rb")
            self.task=Task(model=pickle.load(file),logger=logger)
            file.close()
        else : # new model to train
            self.task=Task(logger=logger)
            self.task.weights=Weights()
        if hasattr(self.task,'init'):
            self.task.init()
        self.searcher=Searcher(self.task,beam_width)
        self.step=0

    def __del__(self):
        del self.searcher
    def test(self,test_file):
        """
        测试
        """
        eval=self.task.Eval()
        for line in open(test_file):
            arg=self.task.codec.decode(line.strip())
            raw=arg.get('raw')
            Y=arg.get('Y_a',None)
            y=arg.get('y',None)
            hat_y=self(raw)
            eval(y,hat_y)
        if hasattr(eval,'get_result'):
            self.result_logger.info(eval.get_result())
        else :
            eval.print_result()#打印评测结果
        return eval
    
    def develop(self,dev_file):
        """
        @brief 预测开发集
        """

        self.task.average_weights(self.step)
        eval=self.task.Eval()
        for line in open(dev_file):
            arg=self.task.codec.decode(line.strip())
            if not arg:continue
            raw=arg.get('raw')
            y=arg.get('y',None)
            hat_y=self(raw)
            eval(y,hat_y)
        if hasattr(eval,'get_result'):
            self.result_logger.info(eval.get_result())
        else :
            eval.print_result()#打印评测结果
        self.task.un_average_weights()

        if hasattr(eval,'get_scaler'):
            return eval.get_scaler()


    def save(self,model_file=None):
        """
        保存模型
        """

        if model_file==None : model_file=self.model_file
        if model_file==None : return
        if model_file=='/dev/null' : return

        self.task.average_weights(self.step)

        file=gzip.open(model_file,'wb')
        data=self.task.dump_weights()
        pickle.dump(data,file)
        #pickle.dump(dict(self.task.weights.items()),file)
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
            margins=self.searcher.cal_margins()
            return self.task.gen_candidates(margins,threshold)

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
            self.task.update_moves(std_moves,rst_moves,self.step)

        
    def train(self,training_file,
            iteration=5,peek=-1,
            dev_files=None,keep_data=True):
        """
        训练
        """
        if iteration<=0 and peek <=0 : peek=5

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

        it=0
        best_it=None
        best_scaler=None

        while True :
            if it == iteration : break
            self.result_logger.info("训练集第 \033[33;01m%i\033[1;m 次迭代"%(it+1))
            eval=self.task.Eval()#: 测试用的对象

            for rtn in gen_data():
                y,hat_y=self._learn_sentence(rtn)#根据（输入，输出）学习参数，顺便得到解码结果
                eval(y,hat_y)#根据解码结果和标准输出，评价效果

            if hasattr(eval,'get_result'):
                self.result_logger.info(eval.get_result())
            else :
                eval.print_result()#打印评测结果

            if hasattr(self.task,'report'):
                self.task.report()
            
            if dev_files:
                #self.result_logger.info("使用开发集 %s 评价当前模型效果"%(dev_file))
                for dev_id,dev_file in enumerate(dev_files) :
                    scaler=self.develop(dev_file)
                    if dev_id==0 :
                        if best_scaler==None or (scaler and best_scaler<scaler) :
                            best_it=it
                            best_scaler=scaler
            it+=1
            if peek>=0 and it-best_it>peek : break
    def __del__(self):
        del self.task


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
