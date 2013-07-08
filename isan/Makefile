all: common/pushdown.so common/dfabeam.so common/first_order_linear.so common/feature_dict.so

gcc= g++ -I /usr/include/python3.2mu -shared -fPIC -O3 -std=c++0x -I .. -Wno-deprecated -g

headers=common/*.hpp utls/*.hpp

common/pushdown.so:  common/python_interface.cc  ${headers}
	${gcc} common/python_interface.cc -o common/pushdown.so \
		-D REDUCE -D __MODULE_NAME=pushdown

common/dfabeam.so:   common/python_interface.cc  ${headers}
	${gcc} common/python_interface.cc -o common/dfabeam.so \
		-D __MODULE_NAME=dfabeam

common/first_order_linear.so: common/first_order_linear/first_order_linear.cc \
			common/first_order_linear/decoder.h
	${gcc} $< -o $@

common/feature_dict.so: common/feature_dict.cc 
	${gcc} $< -o $@
