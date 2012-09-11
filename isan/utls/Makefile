cxx=g++ -O3 -I ~/isan/ -I /usr/include/python3.2mu -shared -fPIC

all: dat


dat: dat.cc *.hpp ../common/*.hpp
	$(cxx) -g -o dat.so dat.cc
