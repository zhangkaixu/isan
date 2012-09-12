#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include <algorithm>
#include "isan/common/common.hpp"
#include "dat.hpp"

using namespace isan;

static PyObject *
make_dat(PyObject *self, PyObject *arg){
    std::cout<<"hello\n";

    PyObject * py_list;
    PyArg_ParseTuple(arg, "O", &py_list);
    std::vector<std::pair<Dict_Item, Score> > list;
    list.clear();


    long size=PySequence_Size(py_list);
    std::cerr<<"list size: "<<size<<"\n";
    PyObject * tri;
    for(int i=0;i<size;i++){
        tri=PyList_GetItem(py_list,i);
        list.push_back(std::pair<Dict_Item, Score>());
        list.back().first=Dict_Item(PyTuple_GET_ITEM(tri,0));
        list.back().second=PyLong_AsLong(PyTuple_GET_ITEM(tri,1));
    };

    std::sort(list.begin(),list.end(),item_cmp);
    DATMaker dm;
    dm.make_dat(list,0);
    dm.shrink();
    std::cout<<dm.dat_size<<"\n";
    std::cout<<(dm.dat)[dm.match(list[3].first)].base<<"\n";
    Py_INCREF(Py_None);
    return Py_None;
};

static PyMethodDef datMethods[] = {
    {"make",  make_dat, METH_VARARGS,""},
    //{"delete",  interface_delete, METH_O,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef datmodule = {
   PyModuleDef_HEAD_INIT,
   "dat",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   datMethods
};

PyMODINIT_FUNC
PyInit_dat(void)
{
    return PyModule_Create(&datmodule);
};
