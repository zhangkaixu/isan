一三 (isan)
====

> “举一隅不以三隅反，则不复也” ——《论语·述而》

一个数据驱动的中文处理工具，可进行**中文分词**（以后会实现 *词性标注* 、 *句法分析* ）。涵盖**训练**、**测试**、**预测**等各阶段的开源代码，适合**实验室使用**。

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

## 动作、状态、特征