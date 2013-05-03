#!/bin/sh
python setup.py build_ext --inplace
g++ -I /usr/include/python3.2mu -shared -fPIC -O3 -std=c++0x -I .. -Wno-deprecated -g -o default_dep0.so default_dep0.c
