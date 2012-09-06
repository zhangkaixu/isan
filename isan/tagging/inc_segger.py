import isan.tagging.default_segger as segger
from isan.common.perceptrons import Base_Model as Model
"""
一个增量搜索模式的中文分词模块
"""


class Segmentation_Space(segger.Segger):
    def __init__(self,beam_width=8):
        self.beam_width=beam_width
        self.weights={}




