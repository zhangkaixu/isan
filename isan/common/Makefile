all: pushdown.so dfabeam.so
pushdown.so: pushdown.cc *.hpp
	g++ pushdown.cc -I /usr/include/python3.2mu -shared -o pushdown.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated

dfabeam.so: dfabeam.cc *.hpp
	g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
