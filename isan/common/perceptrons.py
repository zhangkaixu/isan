#!/usr/bin/python3
import sys
import pickle

class Model(object):
    name="平均感知器"
    def __init__(self,model_file,schema=None,Searcher=None,beam_width=8,**conf):
        """
        初始化
        schema： 如果不设置，则读取已有模型。如果设置，就是学习新模型
        """
        self.beam_width=beam_width;
        self.conf=conf
        if schema==None:
            file=open(model_file,"rb")
            self.schema=pickle.load(file)
            file.close()
        else:
            self.model_file=model_file
            self.schema=schema
            self.schema.weights={}
        if hasattr(self.schema,'init'):
            self.schema.init()
        self.searcher=Searcher(self.schema,beam_width)
        for k,v in self.schema.weights.items():
            self.searcher.set_action(k,v)
        self.step=0

    def __del__(self):
        del self.searcher
    def test(self,test_file):
        """
        测试
        """
        self.searcher.make_dat()
        eval=self.schema.Eval()
        for line in open(test_file):
            arg=self.schema.codec.decode(line.strip())
            raw=arg.get('raw')
            Y=arg.get('Y_a',None)
            y=arg.get('y',None)
            hat_y=self(raw,Y)
            eval(y,hat_y)
        eval.print_result()
        return eval
    def develop(self,dev_file):
        self.searcher.average_weights(self.step)
        eval=self.schema.Eval()
        for line in open(dev_file):
            arg=self.schema.codec.decode(line.strip())
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
        for k,v in self.searcher.export_weights():
            self.schema.weights.setdefault(k,{}).update(v)
        file=open(self.model_file,'wb')
        pickle.dump(self.schema,file)
        file.close()
    def search(self,raw,Y=None):
        self.schema.set_raw(raw,Y)
        self.searcher.set_raw(raw)
        return self.searcher.search()

    def __call__(self,raw,Y=None):
        """
        解码，读入生句子，返回词的数组
        """
        rst_actions=self.search(raw,Y)
        hat_y=self.schema.actions_to_result(rst_actions,raw)
        return hat_y
    def _learn_sentence(self,arg):
        """
        学习，根据生句子和标准分词结果
        """
        raw=arg.get('raw')
        y=arg.get('y',None)
        Y_a=arg.get('Y_a',None)
        
        #学习步数加一
        self.step+=1
        if self.step%100==0:
            #print('*',end='')
            #sys.stdout.flush()
            pass


        #get result actions
        rst_actions=self.search(raw,Y_a)#得到解码后动作
        hat_y=self.schema.actions_to_result(rst_actions,raw)#得到解码后结果

        #get standard actions
        std_actions=self.schema.result_to_actions(y)#得到标准动作

        #update
        #if y!=hat_y:#如果动作不一致，则更新
        if std_actions!=rst_actions:#如果动作不一致，则更新
            self.update(std_actions,rst_actions)
        return y,hat_y
    def update(self,std_actions,rst_actions):
        for stat,action in zip(self.schema.actions_to_stats(std_actions),std_actions):
            self.searcher.update_action(stat,action,1,self.step)
        for stat,action in zip(self.schema.actions_to_stats(rst_actions),rst_actions):
            self.searcher.update_action(stat,action,-1,self.step)

        
    def train(self,training_file,iteration=5,dev_file=None):
        """
        训练
        """
        for it in range(iteration):#迭代整个语料库
            print("训练集第 \033[33;01m%i\033[1;m 次迭代"%(it+1),file=sys.stderr)
            eval=self.schema.Eval()#测试用的对象
            if type(training_file)==str:training_file=[training_file]
            for t_file in training_file:
                for line in open(t_file):#迭代每个句子
                    rtn=self.schema.codec.decode(line.strip())#得到标准输出
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
        y=arg.get('y',None)
        Y_a=arg.get('Y_a',None)
        Y_b=arg.get('Y_b',None)
        
        #学习步数加一
        self.step+=1
        if self.step%100==0:
            pass

        #get result actions
        rst_actions=self.search(raw,Y_a)#得到解码后动作
        hat_y=self.schema.actions_to_result(rst_actions,raw)#得到解码后结果

        if not self.schema.is_belong(hat_y,Y_b): #y!=hat_y:#如果动作不一致，则更新
            if y and not Y_b:
                std_actions=self.schema.result_to_actions(y)#得到标准动作
            else:
                std_actions=self.search(raw,Y_b)
            self.update(std_actions,rst_actions)
        return y,hat_y
