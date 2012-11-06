#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/searcher.hpp"
#include "isan/common/general_types.hpp"
#include "isan/common/weights.hpp"
#include "isan/common/decoder.hpp"
#include "isan/common/python_interface.hpp"
using namespace isan;

static PyObject *
search(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject *py_init_states;
    PyArg_ParseTuple(arg, "LO", &interface,&py_init_states);
    
    std::vector<State_Type> init_states;
    
    for(int i=0;i<PyList_GET_SIZE(py_init_states);i++){
        init_states.push_back(State_Type(PyList_GET_ITEM(py_init_states,i)));
    };

    std::vector<Alpha_Type* > result_alphas;
    
    (*interface->push_down)(
            init_states,
            result_alphas);

    PyObject * rtn_list=PyList_New(result_alphas.size());
    for(int i=0;i<result_alphas.size();i++){
        PyList_SetItem(rtn_list,i,pack_alpha(result_alphas[i]));
    }
    return rtn_list;
};

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
searcher_new(PyObject *self, PyObject *arg)
{
    PyObject * py_early_stop_callback;
    PyObject * py_state_cb;
    PyObject * py_feature_cb;
    int beam_width;
    PyArg_ParseTuple(arg, "iOOO", 
            &beam_width,
            &py_early_stop_callback,
            &py_state_cb,
            &py_feature_cb);
    Interface* interface=new Interface(
            beam_width,
            py_early_stop_callback,
            py_state_cb,
            py_feature_cb);
    return PyLong_FromLong((long)interface);
};

/** stuffs about the module def */
static PyMethodDef dfabeamMethods[] = {
    {"new",  searcher_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"set_raw",  set_raw, METH_VARARGS,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  set_weights, METH_VARARGS,""},
    {"update_action",  update_weights, METH_VARARGS,""},
    {"export_weights",  export_weights, METH_VARARGS,""},
    {"make_dat",  make_dat, METH_VARARGS,""},
    {"average_weights", average_weights , METH_VARARGS,""},
    {"un_average_weights", un_average_weights , METH_VARARGS,""},
    {"get_states",  get_states, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef dfabeammodule = {
   PyModuleDef_HEAD_INIT,
   "dfabeam",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   dfabeamMethods
};

PyMODINIT_FUNC
PyInit_dfabeam(void)
{
    return PyModule_Create(&dfabeammodule);
}
