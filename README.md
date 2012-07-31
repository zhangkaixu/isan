isan
====

最简中文处理工具

特点
* 使用平均感知器算法 averaged perceptron
* 使用增量方式解码 incremental decoding, 时间复杂度 `O(n)`

## 增量模型架构

    Action # 解码过程中的原子动作
    Stats -> Action # 依据动作，定义状态
    Features -> Stats # 由状态产生特征供每个动作使用
    Decoder -> Action Stats Features #解码
    Model -> Decoder #模型的训练相关

## 中文分词模块

## 中文句法分析模块

