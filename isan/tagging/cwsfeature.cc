#include <Python.h>
#include <iostream>
#include <vector>
#include "cws.hpp"
/**
 * g++ cwsfeature.c -I /usr/include/python3.2mu -shared -o cwsfeature.so -fPIC -O3

 * */

typedef Chinese_Character chinese_character;


Chinese* real_raw=NULL;

PyObject * raw;
size_t raw_size;
std::vector<Chinese_Character> raw_vector;
PyObject* NAC=PyLong_FromLong(0);


struct Triple{
    char a;
    chinese_character b;
    char c;
};

static PyObject *
cwsfeature_set_raw(PyObject *self, PyObject *new_raw)
{
    raw=new_raw;
    raw_size=PySequence_Size(raw);
    raw_vector.clear();
    for(int i=0;i<raw_size;i++){
        raw_vector.push_back((chinese_character)*PyUnicode_AS_UNICODE(PySequence_GetItem(raw,i)));
    }
    
    if(real_raw)delete real_raw;
    real_raw=new Chinese(raw_size);
    for(int i=0;i<raw_size;i++){
        real_raw->pt[i]=(Chinese_Character)*PyUnicode_AS_UNICODE(PySequence_GetItem(new_raw,i));
    }
    
    Py_INCREF(Py_None);
    
    return Py_None;
};

static PyObject *
get_features(PyObject *self, PyObject *span)
{
    State_Key key(span);
    
    std::vector<String<char> > fv;
    default_feature(*real_raw,key,fv);
    
    PyObject* list=PyList_New(fv.size());
    for(int i=0;i<fv.size();i++){
        PyList_SetItem(list,i,PyBytes_FromStringAndSize(fv[i].pt,fv[i].length));
    }
    return list;
    
};

static PyMethodDef cwsfeatureMethods[] = {
    //{"system",  spam_system, METH_VARARGS,"Execute a shell command."},
    //{"add",  spam_add, METH_O,""},
    {"set_raw",  cwsfeature_set_raw, METH_O,""},
    {"get_features",  get_features, METH_O,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef cwsfeaturemodule = {
   PyModuleDef_HEAD_INIT,
   "cwsfeature",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   cwsfeatureMethods
};

PyMODINIT_FUNC
PyInit_cwsfeature(void)
{
    return PyModule_Create(&cwsfeaturemodule);
}
