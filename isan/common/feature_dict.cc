#include <Python.h>
#include <iostream>
#include <unordered_map>


#define __MODULE_NAME feature_dict
#define __INIT_FUNC(a,b) a##b
#define INIT_FUNC(a,b) __INIT_FUNC(a,b)
#define PYINIT PyInit_
#define STR(x) #x

struct Hash{
    size_t operator()(const PyObject* key) const{
        size_t size=PyUnicode_GET_SIZE(key);
        auto* data=PyUnicode_AS_UNICODE(key);
        size_t hk=0;
        for(int i=0;i<size;i++){
            hk=((hk<<5)+hk)+(*(data++));
        };
        return hk;
    };
};
struct Equal{
    bool operator()( PyObject* left, PyObject* right) const{
        size_t lsize=PyUnicode_GET_SIZE(left);
        size_t rsize=PyUnicode_GET_SIZE(right);
        if(lsize!=rsize)return false;
        auto* ldata=PyUnicode_AS_UNICODE(left);
        auto* rdata=PyUnicode_AS_UNICODE(right);
        for(int i=0;i<lsize;i++){
            if(*(ldata++)!=*(rdata++))return false;
        };
        return true;
    };
};

typedef std::unordered_map<PyObject*,double,Hash ,Equal> Dict;

static PyObject *
module_new(PyObject *self, PyObject *arg)
{
    Dict* dict=new Dict();
    return PyLong_FromLong((long)dict);
};

static PyObject *
dict_size(PyObject *self, PyObject *arg){
    Dict* dict=(Dict*)PyLong_AsLong(arg);
    return PyLong_FromLong(dict->size());
};

static PyObject *
set_weights(PyObject *self, PyObject *arg){
    Dict* dict;
    PyObject * py_dict;
    
    PyArg_ParseTuple(arg, "LO", &dict,&py_dict);

    PyObject *key, *value;
    Py_ssize_t pos = 0;
    
    size_t length;
    while (PyDict_Next(py_dict, &pos, &key, &value)) {
        Py_INCREF(key);
        (*dict)[key]=PyFloat_AsDouble(value);
    };

    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
to_dict(PyObject *self, PyObject *arg){
    Dict* dict=(Dict*)PyLong_AsLong(arg);
    PyObject * py_dict=PyDict_New();
    for(auto it=dict->begin();it!=dict->end();++it){
        PyObject * key=it->first;
        PyObject * value=PyFloat_FromDouble(it->second);
        PyDict_SetItem(py_dict,key,value);
        Py_DECREF(value);
    };
    return py_dict;
};

static PyObject *
clear(PyObject *self, PyObject *arg){
    Dict* dict=(Dict*)PyLong_AsLong(arg);
    for(auto it=dict->begin();it!=dict->end();++it){
        Py_DECREF(it->first);
    }
    dict->clear();
    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
cal_fv(PyObject *self, PyObject *arg){
    Dict* dict;
    PyObject * py_fv;
    
    PyArg_ParseTuple(arg, "LO", &dict,&py_fv);

    long size=PySequence_Size(py_fv);
    
    double score=0;
    
    for(int i=0;i<size;i++){
        PyObject *key=PySequence_GetItem(py_fv,i);
        auto got=dict->find(key);
        if (got!=dict->end()){
            score+=got->second;
        };
        Py_DECREF(key);
    }

    return PyFloat_FromDouble(score);
    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
get(PyObject *self, PyObject *arg){
    Dict* dict;
    PyObject * key;
    
    PyArg_ParseTuple(arg, "LO", &dict,&key);

    
    auto got=dict->find(key);
    if (got!=dict->end()){
        return PyFloat_FromDouble(got->second);
    };

    return PyFloat_FromDouble(0);
};

static PyObject *
update_fv(PyObject *self, PyObject *arg){
    Dict* dict;
    PyObject * py_fv;
    double delta;
    
    
    PyArg_ParseTuple(arg, "LOd", &dict,&py_fv,&delta);

    long size=PySequence_Size(py_fv);
    
    for(int i=0;i<size;i++){
        PyObject *key=PySequence_GetItem(py_fv,i);
        auto got=dict->find(key);
        if (got!=dict->end()){
            got->second+=delta;
        }else{
            Py_INCREF(key);
            (*dict)[key]=delta;
        };
        Py_DECREF(key);
    }

    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
interface_delete(PyObject *self, PyObject *arg){
    Dict* dict=(Dict*)PyLong_AsLong(arg);
    for(auto it=dict->begin();it!=dict->end();++it){
        Py_DECREF(it->first);
    }
    dict->clear();
    delete dict;
    Py_INCREF(Py_None);
    return Py_None;
};

/** stuffs about the module def */
static PyMethodDef interfaceMethods[] = {
    {"new",  module_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"size",  dict_size, METH_O,""},
    {"set_weights",  set_weights, METH_VARARGS,""},
    {"cal_fv",  cal_fv, METH_VARARGS,""},
    {"update_fv",  update_fv, METH_VARARGS,""},
    {"get",  get, METH_VARARGS,""},
    {"to_dict",  to_dict, METH_O,""},
    {"clear",  clear, METH_O,""},
    //{"set_raw",  set_raw, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef module_struct = {
   PyModuleDef_HEAD_INIT,
   STR(__MODULE_NAME),   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   interfaceMethods
};

PyMODINIT_FUNC
INIT_FUNC(PYINIT,__MODULE_NAME) (void)
{
    return PyModule_Create(&module_struct);
}
