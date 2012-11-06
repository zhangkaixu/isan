#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#define REDUCE
#include "isan/common/searcher.hpp"
#include "isan/common/general_types.hpp"
#include "isan/common/decoder.hpp"
#include "isan/common/python_interface.hpp"


using namespace isan;



static PyObject *
get_states(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyArg_ParseTuple(arg, "L", &interface);
    interface->push_down->cal_betas();

    std::vector<State_Type > states;
    std::vector<Score> scores;

    interface->push_down->get_states(states,scores);

    PyObject * list=PyList_New(states.size());
    for(int i=0;i<states.size();i++){
        PyList_SetItem(list,i,
                    PyTuple_Pack(2,states[i].pack(),PyLong_FromLong(scores[i]))
                );
    };
    return list;

};



static PyObject *
pushdown_new(PyObject *self, PyObject *arg)
{
    PyObject * py_early_stop_callback;
    PyObject * py_shift_callback;
    PyObject * py_reduce_callback;
    PyObject * py_feature_cb;
    int beam_width;
    PyArg_ParseTuple(arg, "iOOOO", &beam_width,
            &py_early_stop_callback,
            &py_shift_callback,
            &py_reduce_callback,
            &py_feature_cb);

    Interface* interface=new Interface(beam_width,
            py_early_stop_callback,
            py_shift_callback,
            py_reduce_callback,
            py_feature_cb);
    return PyLong_FromLong((long)interface);
};



/** stuffs about the module def */
static PyMethodDef pushdownMethods[] = {
    {"new",  pushdown_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  set_weights, METH_VARARGS,""},
    {"set_raw",  do_nothing, METH_VARARGS,""},
    {"update_action",  update_weights, METH_VARARGS,""},
    {"average_weights", average_weights , METH_VARARGS,""},
    {"sum_weights", sum_weights , METH_VARARGS,""},
    {"un_average_weights", un_average_weights , METH_VARARGS,""},
    {"export_weights",  export_weights, METH_VARARGS,""},
    {"get_states",  get_states, METH_VARARGS,""},
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


