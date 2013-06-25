#!/usr/bin/python3
"""!
@mainpage

Isan
====
一个中文处理的实验环境

"""


import sys
import argparse
import random
import logging
import re
import shlex

def make_color(s,color='36'):
    return '\033['+color+';01m%s\033[1;m'%s #blue

class ContextFilter(logging.Filter):
    def filter(self, record):
        msg=record.msg
        #print(record.__dict__)
        record.msg=re.sub(r'\033[^m]*m','',msg)
        return True

def command_line(Model,Task,Decoder):

    parser=argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=r"""用于中文自然语言理解的统计机器学习工具包  作者：张开旭""",
            epilog="""不指定任何语料库，从标准输入流中读入，输出到标准输出流
指定了训练集，则使用训练集进行训练，将模型参数写入文件
指定了测试集，则读入测试集进行测试
“举一隅不以三隅反，则不复也” ——《论语·述而》""")
    parser.add_argument('model_file',nargs='?',default='/dev/null',
            help='模型参数文件',metavar=('模型文件'))
    meta_group=parser.add_argument_group('meta')
    meta_group.add_argument('--model',dest='model_module',default=None,
            help='相应的.sh文件中已设置好（如平均感知器模型）',metavar='机器学习模型')
    meta_group.add_argument('--decoder',dest='decoder',default=None,
            help='相应的.sh文件中已设置好（如有向图解码、Shift-Reduce解码）',metavar='解码算法')
    meta_group.add_argument('--task',dest='task',default=None,
            help='相应的.sh文件中已设置好（如分词、句法分析）',metavar='任务')
    parser.add_argument('--train',action='append', help='训练语料库',metavar=('训练集'))
    parser.add_argument('--test',dest='test_file', help='测试用语料库',metavar=('测试集'))
    parser.add_argument('--iteration',dest='iteration',default=5,type=int,
            help='学习迭代次数(default: %(default)s)',metavar='迭代次数')
    parser.add_argument('--beam_width',dest='beam_width',default=8,type=int,
            help='为0时，柱搜索算法变为动态规划算法(default: %(default)s)',metavar="柱宽度")
    parser.add_argument('--penalty',default='0',type=str, help='',metavar="")
    parser.add_argument('--dev',dest='dev_file',default=None,action='append',
            help='开发用语料库',metavar=('开发集'))
    parser.add_argument('--threshold',dest='threshold',type=int,default=0, help='',metavar='阈值')
    parser.add_argument('--seed',type=int,default=None, help='')
    parser.add_argument('--logfile',default='/dev/null',type=str, help='',metavar="")


    parser.add_argument('--task_args',default='',type=str, help='',metavar="")
    a=(shlex.split(' '.join(sys.argv)))[1:]
    args=parser.parse_args(a)

    info_color='34'

    

    logger=logging.getLogger(__name__)
    console=logging.StreamHandler()
    logfile=logging.FileHandler(args.logfile,'w')
    logfile.setLevel(logging.DEBUG)
    logfile.addFilter(ContextFilter())
    console.setLevel(logging.INFO)
    logger.addHandler(console)
    logger.addHandler(logfile)
    logger.setLevel(logging.INFO)



    if args.model_module:
        mod,_,cls=args.model_module.rpartition('.')
        Model=getattr(__import__(mod,globals(),locals(),[cls],0),cls)
    if args.task:
        mod,_,cls=args.task.rpartition('.')
        Task=getattr(__import__(mod,globals(),locals(),[cls],0),cls)
    if args.decoder :
        mod,_,cls=args.decoder.rpartition('.')
        Decoder=getattr(__import__(mod,globals(),locals(),[cls],0),cls)



    name_model=Model.name if hasattr(Model,'name') else '给定学习算法'
    name_decoder=Decoder.name if hasattr(Decoder,'name') else '给定解码算法'
    name_task=Task.name if hasattr(Task,'name') else '给定任务算法'
    logger.info("""模型: %s 解码器: %s 搜索宽度: %s
任务: %s"""
            %(
            make_color(name_model,info_color),
            make_color(name_decoder,info_color),
            make_color(args.beam_width,info_color),
            make_color(name_task,info_color),
            ))
            

    if args.train:
        """如果指定了训练集，就训练模型"""
        model=Model(None,
                    Task(args=args.task_args),
                    Decoder,beam_width=int(args.beam_width),
                    logger=logger,)

        random.seed(args.seed)
        logger.info('随机数种子: %s'%(make_color(str(args.seed))))

        pen=args.penalty
        pen,*pen_values=pen.split(',')
        pen=int(pen)
        pen_values=map(float,pen_values)
        logger.info("正则化惩罚: %s"%(make_color(args.penalty)))
        model.searcher.set_penalty(pen,*pen_values)

        logger.info("由训练语料库%s迭代%s次，训练%s模型保存在%s。"%(make_color(' '.join(args.train)),
                        make_color(args.iteration),
                        name_task,
                        make_color(args.model_file)))
        if args.dev_file :
            logger.info("开发集使用%s"%(make_color(' '.join(args.dev_file))))

        model.train(args.train,int(args.iteration),dev_files=args.dev_file)
        model.save(args.model_file)

    if args.train and not args.test_file:
        exit()

    if not args.train:
        print("使用模型文件%s进行%s"%(make_color(args.model_file),
                    name_task),file=sys.stderr)
    
    model=Model(args.model_file,task=Task(),
                    Searcher=Decoder,beam_width=int(args.beam_width),
                    logger=logger,
                    )
    
    """如果指定了测试集，就测试模型"""
    if args.test_file:
        print("使用已经过%s的文件%s作为测试集"%(name_task,make_color(args.test_file)),file=sys.stderr)
        model.test(args.test_file)
        exit()
    if not args.test_file and not args.train:
        threshold=args.threshold
        print("以 %s 作为输入，以 %s 作为输出"%(make_color('标准输入流'),make_color('标准输出流')),file=sys.stderr)
        if threshold :
            print("输出分数差距在 %s 之内的候选词"%(make_color(threshold*1000)),file=sys.stderr)
        for line in sys.stdin:
            line=line.strip()
            line=model.schema.codec.decode(line)
            raw=line.get('raw','')
            Y=line.get('Y_a',None)
            if threshold :
                print(model.schema.codec.candidates_encode(model(raw,Y,threshold=threshold)))
            else :
                print(model.schema.codec.encode(model(raw,Y)))
    return args
if __name__ == '__main__':
    command_line(None,None,None)

