all: pushdown.so dfabeam.so
pushdown.so: pushdown.cc *.hpp ../utls/*.hpp
	g++ pushdown.cc -I /usr/include/python3.2mu -shared -o pushdown.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated -D REDUCE

dfabeam.so: dfabeam.cc *.hpp ../utls/*.hpp
	g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
