#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/common.hpp"
#include "isan/common/weights.hpp"
#include "isan/common/searcher.hpp"
#include "isan/common/decoder.hpp"
namespace isan{
typedef General_Interface<State_Info_s> Interface;
};
#include "isan/common/python_interface.hpp"


using namespace isan;






static PyObject *
pushdown_new(PyObject *self, PyObject *arg)
{
    PyObject * py_init_stat;
    PyObject * py_shift_callback;
    PyObject * py_reduce_callback;
    PyObject * py_feature_cb;
    int beam_width;
    PyArg_ParseTuple(arg, "iOOOO", &beam_width,&py_init_stat,
            &py_shift_callback,&py_reduce_callback,
            &py_feature_cb);
    State_Type* init_key = NULL;
    init_key = new State_Type(py_init_stat);

    Interface* interface=new Interface(*init_key,beam_width,
            py_shift_callback,py_reduce_callback,
        py_feature_cb);
    delete init_key;
    return PyLong_FromLong((long)interface);
};


static PyObject *
search(PyObject *self, PyObject *arg)
{

    Interface* interface;
    unsigned long steps;
    PyArg_ParseTuple(arg, "LL", &interface,&steps);

    std::vector<Action_Type> result;
    (*interface->push_down)(interface->init_state,steps,result);

    PyObject * list=PyList_New(result.size());
    for(int i=0;i<result.size();i++){
        PyList_SetItem(list,i,PyLong_FromUnsignedLong(result[i]));
    }
    
    return list;
};


/** stuffs about the module def */
static PyMethodDef pushdownMethods[] = {
    {"new",  pushdown_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  set_weights, METH_VARARGS,""},
    {"update_action",  update_weights, METH_VARARGS,""},
    {"export_weights",  export_weights, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef pushdownmodule = {
   PyModuleDef_HEAD_INIT,
   "dfabeam",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   pushdownMethods
};

PyMODINIT_FUNC
PyInit_pushdown(void)
{
    return PyModule_Create(&pushdownmodule);
}


