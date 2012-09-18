#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/searcher.hpp"
#include "isan/common/weights.hpp"
#include "isan/common/decoder.hpp"
namespace isan{
typedef General_Interface<State_Info_t> Interface;
};
#include "isan/common/python_interface.hpp"
using namespace isan;


static PyObject *
search(PyObject *self, PyObject *arg)
{

    Interface* interface;
    unsigned long steps;
    PyArg_ParseTuple(arg, "LL", &interface,&steps);
    
    std::vector<Action_Type> result;
    interface->push_down->call(interface->init_state,steps,result);

    PyObject * list=PyList_New(result.size());
    
    for(int i=0;i<result.size();i++){
        PyList_SetItem(list,i,PyLong_FromLong(result[i]));
    }
    //std::cout<<"searchend\n";
    return list;
};


static PyObject *
searcher_new(PyObject *self, PyObject *arg)
{
    PyObject * py_init_stat;
    PyObject * py_state_cb;
    PyObject * py_feature_cb;
    int beam_width;
    PyArg_ParseTuple(arg, "iOOO", &beam_width,&py_init_stat,&py_state_cb,&py_feature_cb);
    std::cout<<PyLong_Check(py_feature_cb)<<"\n";

    General_State_Generator * shifted_state_generator;
    General_Feature_Generator * feature_generator;
    feature_generator=(General_Feature_Generator*) PyLong_AsUnsignedLong(py_feature_cb);
    shifted_state_generator=(General_State_Generator *) PyLong_AsUnsignedLong(py_state_cb);

    State_Type* init_state = NULL;
    init_state = new State_Type(py_init_stat);
    
    Interface* interface=new Interface(*init_state,beam_width, 
            shifted_state_generator,
            feature_generator);
    delete init_state;
    
    return PyLong_FromLong((long)interface);
};




static PyObject *
my_set_raw(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject *new_raw;
    PyArg_ParseTuple(arg, "LO", &interface,&new_raw);
    long raw_size=PySequence_Size(new_raw);
    
    Chinese raw(raw_size);
    for(int i=0;i<raw_size;i++){
        PyObject *tmp=PySequence_GetItem(new_raw,i);
        raw.pt[i]=(Chinese_Character)*PyUnicode_AS_UNICODE(tmp);
        Py_DECREF(tmp);
    }
    interface->set_raw(raw);
    interface->feature_generator->raw=interface->raw;
    Py_INCREF(Py_None);
    
    return Py_None;
};



/** stuffs about the module def */
static PyMethodDef cwssearcherMethods[] = {
    {"new",  searcher_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"set_raw",  my_set_raw, METH_VARARGS,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  set_weights, METH_VARARGS,""},
    {"update_action",  update_weights, METH_VARARGS,""},
    {"export_weights",  export_weights, METH_VARARGS,""},
    {"average_weights", average_weights , METH_VARARGS,""},
    {"make_dat",  make_dat, METH_VARARGS,""},
    {"un_average_weights", un_average_weights , METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef cwssearchermodule = {
   PyModuleDef_HEAD_INIT,
   "seggersearcher",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   cwssearcherMethods
};

PyMODINIT_FUNC
PyInit_cwssearcher(void)
{
    return PyModule_Create(&cwssearchermodule);
}
