#!/usr/bin/python3
import isan.tagging.inc_segger as inc_segger
import argparse


def make_green(s):
    return '\033[32;01m%s\033[1;m'%s

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="分词模型")
    parser.add_argument('training_file',help='训练文件')
    parser.add_argument('model_file',help='模型文件')
    parser.add_argument('-i','--iteration',help='模型迭代次数',dest='iteration',default='5')
    #parser.add_argument('-d','--diff',help='指定以html格式输出的显示差异的文件的名字',dest='diff_file')
    args=parser.parse_args()
    #print(args)
    print("由训练语料库%s迭代%s次，训练分词模型保存在%s。"%(make_green(args.training_file),
                    make_green(args.iteration),
                    make_green(args.model_file)))
    model=inc_segger.Model(args.model_file,
                inc_segger.Defalt_Actions(
                )
        )
    model.train(args.training_file,int(args.iteration))
    model.save()
    
    """ 
    model=inc_segger.Model("inc_segger_test.model")
    model.test("test.seg")
    
    
    print(model("就是这么简单"))
    print(model("厉害的武功秘籍都需要相应的内功基础"))
    """
