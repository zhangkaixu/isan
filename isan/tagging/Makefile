all: cwsfeature.so dfabeam.so

cwsfeature.so: cwsfeature.c
	g++ cwsfeature.c -I /usr/include/python3.2mu -shared -o cwsfeature.so -fPIC -O3

dfabeam.so: dfabeam.cc dfa_beam_searcher.cc
	g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3
