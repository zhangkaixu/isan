上手
=============

在此以Ubuntu操作系统为例，介绍如何安装和使用 isan 。

下载与编译
----------------------

首先，需要安装必要的软件包，在命令行下安装

.. code-block:: bash

    sudo apt-get install gcc make python3 python3-dev git python3-numpy

.. note::

    本工具使用的是python3，与最常用的python版本python2不太兼容。

然后选好路径，使用下载 isan 源代码，编译::

    git clone https://github.com/zhangkaixu/isan.git
    cd isan
    make

如果编译正确，就说明已经可以使用了。

使用训练好的模型
----------------------

以中文分词为例, 下载一个训练好的模型文件::

    wget http://t.cn/zQxy95O -O ctb.seg.gz

试试分词::

    echo '厦门大学' | ./isan.sh seg ctb.seg.gz

其中 `isan.sh` 是用来启动isan及其常用任务的脚本。 `seg` 是一个基于字标注的分词任务。 `ctb.seg.gz` 是刚才下载的对应的模型。 运行后将会得到这样的输出::

    厦门 大学

程序从标准输入流读入输入数据，将结果输出到标准输出流。可以这样执行::

    ./isan.sh seg ctb.seg.gz < input_file > output_file

