基本操作
================

模型的训练、测试和使用
---------------------------------------

命令行及参数
++++++++++++++++++++++++

主要命令均通过调用 ``./isan.py`` 完成。

许多已实现的模型有一些固定的参数，可以使用 ``./isan.sh`` 更方便的调用， 基本操作使用后者即可。

.. code-block:: bash

    ./isan.sh model-name [model-file] [ other args ]

其中 ``model-name`` 是模型名字， 如 ``seg`` 是一个基于字标注的模型，可用于进行分词或者分词词性标注， ``cws`` 是一个基于词的分词模型， ``dep`` 是一个依存句法分析模型。

``model-file`` 是模型参数文件。 如果是训练任务，可为空，表示训练之后不保存模型参数。

本小节将涉及的其它参数有：

* ``--train training-data`` 使用指定的训练集文件训练模型
* ``--test test-data`` 训练完后使用测试集测试模型效果
* ``--dev dev-data`` 每次训练迭代后使用开发集评价模型效果
* ``--iteration iter`` 指定训练迭代次数

主要使用场合：

* **训练模型** ： 指定了 ``--train`` 参数，则训练一个新模型保存在 ``model-name`` ， 可同时再使用 ``--test`` ``--dev`` 等参数
* **测试模型** ： 不指定 ``--train`` 参数， 但指定 ``--test`` 参数
* **使用模型** ： 不指定 ``--train`` 参数， 也不指定 ``--test`` 参数， 则从标准输入流中读入输入，将输出输出到标准输入流。

实例
++++++++++++++++++++++++

可以用中文分词任务试试isan如何工作。下载一个可供实验用的SIGHAN05中文分词语料库::

    wget http://www.sighan.org/bakeoff2005/data/icwb2-data.rar
    sudo apt-get install unrar
    mkdir sighan05; unrar e icwb2-data.rar sighan05
    ln -s sighan05/msr_test_gold.utf8 train.seg
    ln -s sighan05/msr_test_gold.utf8 test.seg


试着训练和测试::

    ./isan.sh seg model.gz --train test.seg
    ./isan.sh seg model.gz --test test.seg

接下来就可以试着真枪实弹地来一次，在MSR的训练集上迭代30次训练模型，每次迭代都将测试集作为开发集检查一下模型性能::

    ./isan.sh seg model.gz --train train \
            --dev test.seg --iteration 15

需要一些耐心等待程序结束。

会得到类似这样的结果::

    标准: 8008 输出: 8057 seg正确: 7811 正确: 7811 seg_f1: 0.9724 tag_f1: 0.9724 ol: 11 时间: 0.2762 (49733字/秒)

可以看到分词F值为0.9724。

还可以使用 ``./isan/tagging/eval.py`` 这个工具, 直接比较两个分词结果::

    sed 's/\ //g' test.seg | ./isan.sh seg ctb.seg.gz > result.seg
    ./isan/tagging/eval.py test.seg result.seg
    

已实现的模型
--------------------------------

.. _trained_model_parameter_list:

已训练模型列表
++++++++++++++++++++++++++++++++

中文分词 使用 ``wget http://t.cn/zQxy95O -O ctb.seg.gz``  获取，使用 ``./isan.sh seg ctb.seg.gz`` 启动

中文分词词性标注  使用 ``http://t.cn/zQxg4lX -O ctb.tag.gz`` 获取， 使用 ``./isan.sh seg ctb.tag.gz`` 启动
