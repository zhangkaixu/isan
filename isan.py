#!/usr/bin/python3
import sys
import argparse

def make_color(s,color='36'):
    return '\033['+color+';01m%s\033[1;m'%s #blue


def command_line(Model,Task,Decoder):

    parser=argparse.ArgumentParser(description="")
    parser.add_argument('model_file',help='模型文件')
    parser.add_argument('--train',help='训练文件',action='append')
    parser.add_argument('-i','--iteration',help='模型迭代次数',dest='iteration',default='5')
    parser.add_argument('-M','--model',help='模型',dest='model_module',default=None)
    parser.add_argument('-D','--decoder',help='搜索算法',dest='decoder',default=None)
    parser.add_argument('-T','--task',help='任务',dest='task',default=None)
    parser.add_argument('--test',help='测试用文件',dest='test_file')
    parser.add_argument('--dev',help='开发用文件',dest='dev_file',default=None)
    parser.add_argument('--beam_width',help='搜索宽度',dest='beam_width',default='8')
    args=parser.parse_args()
    """如果指定了训练集，就训练模型"""
    info_color='34'


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
    print("""模型: %s 解码器: %s 搜索宽度: %s
任务: %s"""
            %(
            make_color(name_model,info_color),
            make_color(name_decoder,info_color),
            make_color(args.beam_width,info_color),
            make_color(name_task,info_color),
            ),file=sys.stderr)
            
    if args.train:
        print("由训练语料库%s迭代%s次，训练%s模型保存在%s。"%(make_color(' '.join(args.train)),
                        make_color(args.iteration),
                        name_task,
                        make_color(args.model_file)),file=sys.stderr)
        model=Model(args.model_file,
                    Task(),
                    Decoder,beam_width=int(args.beam_width),
            )
        model.train(args.train,int(args.iteration),dev_file=args.dev_file)
        model.save()

    if args.train and not args.test_file:
        exit()
    if not args.train:
        print("使用模型文件%s进行%s"%(make_color(args.model_file),
                    name_task),file=sys.stderr)
    
    model=Model(args.model_file,
                    Searcher=Decoder,beam_width=int(args.beam_width)
                    )
    
    """如果指定了测试集，就测试模型"""
    if args.test_file:
        print("使用已经过%s的文件%s作为测试集"%(name_task,make_color(args.test_file)),file=sys.stderr)
        model.test(args.test_file)
        exit()
    if not args.test_file and not args.train:
        print("以%s作为输入，以%s作为输出"%(make_color('标准输入流'),make_color('标准输出流')),file=sys.stderr)
        for line in sys.stdin:
            line=line.strip()
            print(*model(line))
    return args
if __name__ == '__main__':
    command_line(None,None,None)

