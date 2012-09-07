all: dfabeam.so

dfabeam.so: dfabeam.cc cws.hpp ../common/common.hpp ../common/weights.hpp ../common/searcher.hpp ../common/decoder.hpp
	g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
