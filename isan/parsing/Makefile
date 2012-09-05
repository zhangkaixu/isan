all: pushdown.so

pushdown.so: pushdown.cc push_down.hpp ../common/common.hpp ../common/weights.hpp
	g++ pushdown.cc -I /usr/include/python3.2mu -shared -o pushdown.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
