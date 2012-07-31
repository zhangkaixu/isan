一三 (isan)
====

> “举一隅不以三隅反，则不复也” ——《论语·述而》

一个数据驱动的中文处理工具

特点

* 可进行**中文分词**、**词性标注**（以后会实现 *句法分析* ）
* 涵盖**训练**、**测试**、**预测**等各阶段的开源代码
* 框架统一、代码简单、易于扩展，适合**实验室**使用或研发原型系统
* 使用**增量方式解码**，时间复杂度 `O(n)`

# 使用

## 安装

运行本软件需要Linux操作系统和Python3。（如果是Windows操作系统需要对代码做一些修改）

在[github](https://github.com/zhangkaixu/isan)上下载[压缩包](https://github.com/zhangkaixu/isan/zipball/master)解压得到源代码，或者安装git后使用`git clone https://github.com/zhangkaixu/isan.git`

## 基本命令行用法

例如中文分词的基本命令行用法如下：

    ./cws.py model_file [--train training_file] [--test test_file]
        [--iteration iter] [--beam_width w]

其中：

* `model_file` 是用以存储模型参数的文件
* `training_file` 如果给出，会使用该文件训练模型
* `test_file` 如果给出，会使用已有模型或新训练的模型在该文件上进行测试
* 如果 `training_file` 和 `test_file` 均未给出，则对标准输入流中的文本进行分词，输出结果到标准输出流
* `iter` 用来指定训练时的迭代次数
* `w` 用来指定柱搜索解码中的搜索宽度（柱宽度）

词性标注的基本命令行用法相同，只需要将`cws.py`替换为`tag.py`（当然部分功能尚未实现）。

## 输入输出格式

每个句子一行

* 原始句子 `材料利用率高。`
* 分词结果 `材料 利用率 高 。`
* 词性标注结果 `材料_NN 利用率_NN 高_VA 。_PU`

例如在分词`./cws.py`命令中，`training_file` 、 `test_file` 以及预测阶段的输出的格式均是使用的分词结果格式， 预测阶段的输入格式是原始句子格式。


# 增量模型架构

    Action # 解码过程中的原子动作
    Stats -> Action # 依据动作，定义状态
    Features -> Stats # 由状态产生特征供每个动作使用
    Decoder -> Action Stats Features #解码
    Model -> Decoder #模型的训练相关
