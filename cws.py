#!/usr/bin/python3
from isan.common.command_line import *
from isan.common.perceptrons import Base_Model as Model
from isan.tagging.default_segger import Segger as Segger
from isan.tagging.dfa import DFA as Searcher


if __name__=="__main__":
    command_line('分词',Model,Segger,Searcher)
