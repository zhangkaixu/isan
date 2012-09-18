all : cwssearcher.so cwstask.so

cwssearcher.so: cwssearcher.cc ../common/*.hpp ../utls/*.hpp
	g++ cwssearcher.cc -I /usr/include/python3.2mu -shared -o cwssearcher.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated


cwstask.so: cwstask.cc ../common/*.hpp ../utls/*.hpp
	g++ cwstask.cc -I /usr/include/python3.2mu -shared -o cwstask.so -fPIC -O3 -std=c++0x -I ../.. -Wno-deprecated
