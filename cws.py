#!/usr/bin/python3
from isan.common.command_line import *
import isan.tagging.inc_segger as inc_segger


if __name__=="__main__":
    command_line('分词',inc_segger.Model,inc_segger.Segmentation_Space)
