all: dfabeam.so

dfabeam.so: dfabeam.cc dfa_beam_searcher.hpp cws.hpp ../common/common.hpp
	g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
