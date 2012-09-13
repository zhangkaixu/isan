# 准备开始

以Ubuntu为例，介绍如何配置和使用**isan**。

首先，需要安装必要的软件包，包括gcc编译器，Python3，Python3-dev和git，在命令行下安装：

    sudo apt-get install gcc
    sudo apt-get install python3
    sudo apt-get install python3-dev
    sudo apt-get install git

使用git下载**isan**源代码，编译。

    git clone https://github.com/zhangkaixu/isan.git
    cd isan
    make

下载可供实验用的SIGHAN05语料库。

    wget http://www.sighan.org/bakeoff2005/data/icwb2-data.rar
    sudo apt-get install unrar
    mkdir sighan05
    unrar e icwb2-data.rar sighan05
    
试着训练和测试。
    
    ./cws.py test.bin --train sighan05/msr_test_gold.utf8
    ./cws.py test.bin --test sighan05/msr_test_gold.utf8
    