#!/usr/bin/python3
import isan.tagging.inc_segger as inc_segger
import argparse
import sys

def make_color(s):
    #return '\033[32;01m%s\033[1;m'%s  #green
    #return '\033[35;01m%s\033[1;m'%s #purple
    return '\033[36;01m%s\033[1;m'%s #blue

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="分词模型")
    parser.add_argument('model_file',help='模型文件')
    parser.add_argument('--train',help='训练文件',action='append')
    parser.add_argument('-i','--iteration',help='模型迭代次数',dest='iteration',default='5')
    parser.add_argument('--test',help='测试用文件',dest='test_file')
    parser.add_argument('--beam_width',help='搜索宽度',dest='beam_width',default='8')
    args=parser.parse_args()
    """如果指定了训练集，就训练模型"""
    print("使用柱搜索，柱宽度为%s"%(make_color(args.beam_width)))
            
    if args.train:
        print("由训练语料库%s迭代%s次，训练分词模型保存在%s。"%(make_color(' '.join(args.train)),
                        make_color(args.iteration),
                        make_color(args.model_file)),file=sys.stderr)
        model=inc_segger.Model(args.model_file,
                    inc_segger.Defalt_Actions(beam_width=int(args.beam_width)
                    )
            )
        model.train(args.train,int(args.iteration))
        model.save()

    if args.train and not args.test_file:
        exit()
    if not args.train:
        print("使用模型文件%s分词"%(make_color(args.model_file)),file=sys.stderr)
    
    model=inc_segger.Model(args.model_file,
                inc_segger.Defalt_Actions(beam_width=int(args.beam_width)
                )
        )
    model=inc_segger.Model(args.model_file)
    
    """如果指定了测试集，就测试模型"""
    if args.test_file:
        print("使用已分词的文件%s作为测试集"%(make_color(args.test_file)),file=sys.stderr)
        model.test(args.test_file)
        exit()
    if not args.test_file and not args.train:
        print("以%s作为输入，以%s作为输出"%(make_color('标准输入流'),make_color('标准输出流')),file=sys.stderr)
        for line in sys.stdin:
            line=line.strip()
            print(*model(line))
