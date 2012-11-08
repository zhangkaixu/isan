all: common/pushdown.so common/dfabeam.so tagging/cwstask.so

gcc= g++ -I /usr/include/python3.2mu -shared -fPIC -O3 -std=c++0x -I .. -Wno-deprecated -g

headers=common/*.hpp utls/*.hpp

common/pushdown.so:  common/python_interface.cc  ${headers}
	${gcc} common/python_interface.cc -o common/pushdown.so \
		-D REDUCE -D __MODULE_NAME=pushdown

common/dfabeam.so:   common/python_interface.cc  ${headers}
	${gcc} common/python_interface.cc -o common/dfabeam.so \
		-D __MODULE_NAME=dfabeam

tagging/cwstask.so: tagging/cwstask.cc ${headers}
	${gcc} tagging/cwstask.cc -o tagging/cwstask.so


