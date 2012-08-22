#!/usr/bin/python3
import isan.tagging.inc_tagger as inc_tagger
from isan.common.command_line import *

if __name__=="__main__":
    command_line('词性标注',inc_tagger.Model,inc_tagger.Segmentation_Space)
