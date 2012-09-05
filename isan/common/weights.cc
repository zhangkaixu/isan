#include <Python.h>
#include <iostream>
#include <vector>
#include "weights.hpp"
/**
 * g++ weights.cc -I /usr/include/python3.2mu -shared -o weights.so -fPIC -O3

 * */

typedef String<char> CX;

typedef Weights<CX,int> My_Weights;

static PyObject *
new_weights(PyObject *self, PyObject *arg){
    My_Weights* weights=new My_Weights();
    return PyLong_FromLong((long)weights);
};

static PyObject *
delete_weights(PyObject *self, PyObject *arg){
    delete (My_Weights*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
call(PyObject *self, PyObject *arg){
    
    My_Weights* weights=(My_Weights*)PyLong_AsLong(PySequence_GetItem(arg,0));
    PyObject * list = PySequence_GetItem(arg,1);
    
    std::vector<CX> fv;
    
    long size=PySequence_Size(list);
    char* buffer;
    size_t length;
    for(int i=0;i<size;i++){
        PyObject * bytes=PySequence_GetItem(list,i);
        PyBytes_AsStringAndSize(bytes,&buffer,(Py_ssize_t*)&(length));
        fv.push_back(CX(buffer,length));
        Py_DECREF(bytes);
    };
    Py_DECREF(list);
    
    long value=(*weights)(fv);
    //for(int i=0;i<size;i++){
        //delete[] fv[i].pt;
    //}

    return PyLong_FromLong(value);
    //Py_INCREF(Py_None);
    //return Py_None;
    
};

static PyObject *
update(PyObject *self, PyObject *arg){
    My_Weights* weights=(My_Weights*)PyLong_AsLong(PySequence_GetItem(arg,0));
    
    PyObject * list = PySequence_GetItem(arg,1);
    long delta=PyLong_AsLong(PySequence_GetItem(arg,2));
    long step=PyLong_AsLong(PySequence_GetItem(arg,3));
    std::vector<CX> fv;
    
    long size=PySequence_Size(list);
    char* buffer;
    size_t length;
    for(int i=0;i<size;i++){
        PyObject * bytes=PySequence_GetItem(list,i);
        PyBytes_AsStringAndSize(bytes,&buffer,(Py_ssize_t*)&(length));
        fv.push_back(CX(buffer,length));
        Py_DECREF(bytes);
    };
    Py_DECREF(list);
    
    weights->update(fv,delta,step);
    
    Py_INCREF(Py_None);
    return Py_None;
};

/** stuffs about the module def */
static PyMethodDef weightsMethods[] = {
    //{"system",  spam_system, METH_VARARGS,"Execute a shell command."},
    {"new_weights",  new_weights, METH_O,""},
    {"delete_weights",  delete_weights, METH_O,""},
    {"call",  call, METH_O,""},
    {"update",  update, METH_O,""},
    //{"test_map",  test_map, METH_O,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef weightsmodule = {
   PyModuleDef_HEAD_INIT,
   "weights",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   weightsMethods
};

PyMODINIT_FUNC
PyInit_weights(void)
{
    return PyModule_Create(&weightsmodule);
}
