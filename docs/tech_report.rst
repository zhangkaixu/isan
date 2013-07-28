技术报告
==================

结构分类问题
+++++++++++++++++++++++++++

解码过程

.. math::

    \mathbf{z}=\arg\max_{\mathbf{z}}{f(\mathbf{x},\mathbf{w};\mathbf{z})}

损失函数

.. math::

    \text{loss}(\mathbf{w})=\sum_{i}{f(\mathbf{x}_i,\mathbf{w};\mathbf{z}_i)-f(\mathbf{x}_i,\mathbf{w};\mathbf{y}_i)}

.. note::

    还可以设计其它的损失函数。

参数优化

.. math::

    \mathbf{w}=\arg\min{\text{loss}(\mathbf{w})}

随机梯度下降算法
+++++++++++++++++++++++++++


1. 得到一个训练样本 :math:`(\mathbf{x}_t,\mathbf{y}_t)`
2. 解码得到当前权重下的最优输出 :math:`\mathbf{z}_t=\arg\max_{\mathbf{z}}{f(\mathbf{x}_t,\mathbf{w};\mathbf{z})}`
3. 如果 :math:`\mathbf{z}_t\not=\mathbf{y}_t` 则 :math:`\mathbf{w}\leftarrow \mathbf{w}-\eta \left. \frac{\partial \text{loss}}{\partial \mathbf{w}} \right|_{\mathbf{w}}`
4. 判断是否停止，如不停止跳到步骤1。

感知器算法

平均感知器
----------------------------


Early-update
----------------------------


解码器
+++++++++++++++++++++++++++


类隐马尔可夫解码器
-----------------------------

一阶解码器适合解决当目标函数可按以下形式分解的情况：

.. math::

    f(\mathbf{x};\mathbf{z})=\sum_{i}{g(\mathbf{x};z_i)}+\sum_{i}{h(z_i,z_{i+1})}

一般线性解码器
-----------------------------

.. math::

    f(\mathbf{x};\mathbf{z})=\sum_{i}{h(\mathbf{x};z_i,z_{i+1})}

一般二叉树解码器
-----------------------------

.. math::

    f(\mathbf{x};\mathbf{z})=\sum_{p}{h(\mathbf{x};z_{p},z_{l},z_{r})}+\sum_{l}{g(\mathbf{x};z_{l})}

已实现的方法
+++++++++++++++++++++++++++

基于字标注的分词词性标注
-----------------------------


基于词的中文分词
-----------------------------


基于词图的分词词性标注
-----------------------------


移进-归约依存句法分析
-----------------------------
