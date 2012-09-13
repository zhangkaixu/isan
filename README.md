一三 (isan)
====

> “举一隅不以三隅反，则不复也” ——《论语·述而》

一个数据驱动的中文处理**实验环境**，可进行**中文分词**（以后会实现 *词性标注* 、 *句法分析* ），涵盖**训练**、**测试**、**预测**等各阶段的开源代码。

特点

* 速度**慢**，不为速度牺牲性能，同时保证算法的各个组件的代码容易修改，但理论上保持`O(n)`的时间复杂度。
* 效果**差**，本系统专为实验使用，目标并非实用分词工具，处理真实文本效果并不理想。但可用于设计实用分词系统。
* 使用**难**，虽然不太实用，但有很多“手动功能”，可以通过理解并修改源代码来完成算法和设置的充分修改。

# 运行

## 准备开始

在此以Ubuntu操作系统为例，介绍如何安装和使用**isan**。

首先，需要安装必要的软件包，包括gcc，make，Python3，Python3-dev和git，在命令行下安装：

    sudo apt-get install gcc
    sudo apt-get install make
    sudo apt-get install python3
    sudo apt-get install python3-dev
    sudo apt-get install git

选好路径，使用git下载**isan**源代码，编译。

    git clone https://github.com/zhangkaixu/isan.git
    cd isan
    make

下载一个可供实验用的SIGHAN05中文分词语料库。

    wget http://www.sighan.org/bakeoff2005/data/icwb2-data.rar
    sudo apt-get install unrar
    mkdir sighan05
    unrar e icwb2-data.rar sighan05
    
试着训练和测试，看看程序是否安装正确。
    
    ./cws.py test.bin --train sighan05/msr_test_gold.utf8
    ./cws.py test.bin --test sighan05/msr_test_gold.utf8
    
如果以上一切顺利，将会看到测试结果能有0.99以上的F1值。接下来就可以试着真枪实弹地来一次，在MSR的训练集上迭代15次训练模型，每次迭代都将测试集作为开发集检查一下模型性能。
    
    ./cws.py test.bin --train sighan05/msr_training.utf8 --iteration=15 --dev sighan05/msr_test_gold.utf8
    
可以看到最后效果保持在0.966、0.967左右，一个还算可以的baseline吧。

当然，如果要用**isan**来进行实验，需要对部分源代码进行进一步的修改。

## 基本命令行用法

例如中文分词的基本命令行用法如下：

    ./cws.py model_file [--train training_file] [--test test_file] [--dev dev_file]
        [--iteration iter] [--beam_width w]

其中：

* `model_file` 是用以存储模型参数的文件
* `training_file` 如果给出，会使用该文件训练模型
* `dev_file` 如果给出，会在每次训练迭代之后在`dev_file`上测试模型效果
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

例如在分词`./cws.py`命令中，`training_file` 、 `dev_file`、 `test_file` 以及预测阶段的输出的格式均是使用的分词结果格式， 预测阶段的输入格式是原始句子格式。


# 架构

现以分词模型为例，介绍程序架构。

## 程序架构

首先看看`./cws.py`文件的`import`部分，其包含了模型的三个组成部分：

    from isan.tagging.default_segger import Segger as Segger
    from isan.common.searcher import DFA as Searcher
    from isan.common.perceptrons import Base_Model as Model
    
首先是`Segger`，包含了分词相关的所有代码，仔细阅读[源代码](https://github.com/zhangkaixu/isan/blob/master/isan/tagging/default_segger.py)中的所有内容，修改其中的代码，就能DIY出自己的分词模型。

其次是`Searcher`，是一个解码器，与具体的任务无关。分词使用的是基于状态转移的`DFA`解码器，也就是一个维特比解码器，相同解码器也可完成词性标注等任务。此外模型的特征权重也由Searcher管理。

最后是`Model`，是控制模型学习、预测过程的，与具体的任务和解码器均无关。该例子中使用的是平均感知器算法进行模型的学习和预测。

## 解码过程

解码就是根据**输入**搜索得到**输出**的过程。

### 动作

**isan**是这样建模的。首先定义一个**动作**的集合，解码过程就是根据输入，得到一个动作序列，然后根据输入与动作序列，就能唯一确定输出。因此解码的过程就是根据输入得到动作序列的过程。

在分词例子中，动作有两种，即*分*与*断*，一个有`n`个字的输入，对应的动作序列中有`n+1`个动作，分别表示各个字边界是分还是断。

### 状态

下面的问题是如何依次确定动作序列中每个位置具体的动作。首先引入**状态**这一概念，有一个初始状态，一个状态根据不同的动作转移到下一个不同的状态。最后到终止状态。**isan**根据当前状态确定下一个动作哪个好哪个不好。

### 特征

具体地，由状态和输入可生成每个状态的特征，每个特征-动作二元组对应一个权重。那么对于一个动作，一个状态的`k`个特征就有`k`个权重，它们线性相加就是一个分数，对应着这个动作的优劣。

接下来，回到最开始的解码中确定动作序列的问题上，一个动作序列的的好坏，由序列中每个动作的分数相加得到。解码就是尽量找到分数最高的动作序列，以此生成输出。