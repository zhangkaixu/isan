#include <Python.h>
#include <iostream>
#include "dat.h"
/**
 * g++ spammodule.c -I /usr/include/python3.2mu -shared -o spam.so -fPIC
 * */


using namespace dat;

static PyObject *
cdat_open(PyObject *self, PyObject *args)
{
    char* filename=NULL;
    PyArg_ParseTuple(args,"s",&filename);
    DAT* dat=new DAT(filename);
    return PyLong_FromLong((size_t)dat);

}
static PyObject *
cdat_close(PyObject *self, PyObject *args)
{
    PyObject* handler=NULL;
    PyArg_ParseTuple(args,"O",&handler);
    delete (DAT*)PyLong_AsLong(handler);
	return Py_None;
}
static PyObject *
cdat_get(PyObject *self, PyObject *args)
{
    PyObject* handler=NULL;
    PyObject* py_key=NULL;
    int no_prefix=0;
    PyArg_ParseTuple(args,"OOi",&handler,&py_key,&no_prefix);
    DAT* dat=(DAT*)PyLong_AsLong(handler);
    
    Word key;
    size_t key_size=PySequence_Size(py_key);
    for(size_t i=0;i<key_size;i++){
        key.push_back(*(int*)PyUnicode_AS_UNICODE(PySequence_GetItem(py_key,i)));
    }
    int ind=0;
    if(no_prefix){
        ind=dat->p_match(key);
    }else{
        ind=dat->match(key);
    };
    if (ind==-1) return Py_None;
    return PyLong_FromLong(dat->dat[ind].base);
}
static PyObject *
cdat_set(PyObject *self, PyObject *args)
{
    PyObject* handler=NULL;
    PyObject* py_key=NULL;
    int value=0;
    PyArg_ParseTuple(args,"OOi",&handler,&py_key,&value);
    DAT* dat=(DAT*)PyLong_AsLong(handler);
    
    Word key;
    size_t key_size=PySequence_Size(py_key);
    for(size_t i=0;i<key_size;i++){
        key.push_back(*(int*)PyUnicode_AS_UNICODE(PySequence_GetItem(py_key,i)));
    }
    int ind=dat->p_match(key);
    if (ind==-1) return Py_None;
    dat->dat[ind].base=value;
    return PyLong_FromLong(value);
}
static PyObject *
cdat_inc(PyObject *self, PyObject *args)
{
    PyObject* handler=NULL;
    PyObject* py_key=NULL;
    int value=0;
    int no_prefix=0;
    PyArg_ParseTuple(args,"OOii",&handler,&py_key,&no_prefix,&value);
    DAT* dat=(DAT*)PyLong_AsLong(handler);
    
    Word key;
    size_t key_size=PySequence_Size(py_key);
    for(size_t i=0;i<key_size;i++){
        key.push_back(*(int*)PyUnicode_AS_UNICODE(PySequence_GetItem(py_key,i)));
    }
    //int ind=dat->p_match(key);
    int ind=0;
    if(no_prefix){
        ind=dat->p_match(key);
    }else{
        ind=dat->match(key);
    };
    if (ind==-1) return Py_None;
    dat->dat[ind].base+=value;
    return PyLong_FromLong(dat->dat[ind].base);
}
static PyObject *
cdat_build(PyObject *self, PyObject *args)
{
    PyObject* list=NULL;
    char* filename=NULL;
    PyArg_ParseTuple(args,"sO",&filename,&list);
    DATMaker dm;
    std::vector<DATMaker::KeyValue> lexicon;
    size_t size=PySequence_Size(list);
    for(size_t i=0;i<size;i++){
        lexicon.push_back(DATMaker::KeyValue());
        PyObject* line=PySequence_GetItem(list,i);
        size_t line_size=PySequence_Size(line);
        PyObject* py_key=PySequence_GetItem(line,0);
        DATMaker::KeyValue* kv=&lexicon.back();
        kv->value=(int)PyLong_AsLong(PySequence_GetItem(line,1));
        size_t key_size=PySequence_Size(py_key);
        for(size_t i=0;i<key_size;i++){
            kv->key.push_back(*(int*)PyUnicode_AS_UNICODE(PySequence_GetItem(py_key,i)));
        }
    }
    dm.make_dat(lexicon,true);
    dm.shrink();
    dm.save_as(filename);
    fprintf(stderr,"size of DAT %d\n",(int)dm.dat_size);
	return Py_None;
};


static PyMethodDef cdatMethods[] = {
    {"build",  cdat_build, METH_VARARGS,""},
    {"open",  cdat_open, METH_VARARGS,""},
    {"close",  cdat_close, METH_VARARGS,""},
    {"get",  cdat_get, METH_VARARGS,""},
    {"set",  cdat_set, METH_VARARGS,""},
    {"inc",  cdat_inc, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef cdatmodule = {
   PyModuleDef_HEAD_INIT,
   "spam",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   cdatMethods
};
PyMODINIT_FUNC
PyInit_cdat(void)
{
    return PyModule_Create(&cdatmodule);
}
