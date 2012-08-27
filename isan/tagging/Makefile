all: cwsfeature.so dfabeam.so

cwsfeature.so: cwsfeature.c cws.hpp ../common/common.hpp
	g++ cwsfeature.c -I /usr/include/python3.2mu -shared -o cwsfeature.so -fPIC -O3 -I ../..

dfabeam.so: dfabeam.cc dfa_beam_searcher.hpp cws.hpp ../common/common.hpp
	g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../..
