all: pushdown.so

pushdown.so: pushdown.cc ../common/common.hpp ../common/weights.hpp ../common/searcher.hpp
	g++ pushdown.cc -I /usr/include/python3.2mu -shared -o pushdown.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
