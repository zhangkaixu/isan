all: pushdown.so dfabeam.so
pushdown.so:  python_interface.cc *.hpp ../utls/*.hpp
	g++ python_interface.cc -I /usr/include/python3.2mu -shared -o pushdown.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated\
		-D REDUCE -D __MODULE_NAME=pushdown

dfabeam.so:  python_interface.cc *.hpp ../utls/*.hpp
	#g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
	g++ python_interface.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated\
		-D __MODULE_NAME=dfabeam
