#pragma
#include <Python.h>
#include "isan/common/common.hpp"
#include "isan/common/decoder.hpp"



namespace isan{


static PyObject *
interface_delete(PyObject *self, PyObject *arg){
    delete (Interface*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
set_weights(PyObject *self, PyObject *arg)
{
    Interface* interface;
    int step;
    PyObject * py_action;
    PyObject * py_dict;
    Action_Type action;
    PyArg_ParseTuple(arg, "LBO", &interface,&action,&py_dict);
    
    interface->data->actions[action]=new Default_Weights(py_dict);

    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
update_weights(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject * py_state;
    long delta=0;
    long step=0;
    Action_Type action;
    PyArg_ParseTuple(arg, "LOBii", &interface,&py_state,&action,&delta,&step);
    State_Type state(py_state);
    
    Feature_Vector fv;
    (*(interface->feature_generator))(state,fv);

    auto& actions=interface->data->actions;
    auto got=actions.find(action);
    if(got==actions.end()){
        actions[action]=new Default_Weights();
    };
    (*(interface->data->actions[action])).update(fv,delta,step);
    
    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
average_weights(PyObject *self, PyObject *arg)
{
    
    Interface* interface;
    int step;
    PyArg_ParseTuple(arg, "Li", &interface,&step);
    
    for(auto iter=interface->data->actions.begin();
            iter!=interface->data->actions.end();
            ++iter){
        iter->second->average(step);
    };
    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
make_dat(PyObject *self, PyObject *arg)
{
    
    Interface* interface;
    PyArg_ParseTuple(arg, "L", &interface);
    
    for(auto iter=interface->data->actions.begin();
            iter!=interface->data->actions.end();
            ++iter){
        //iter->second->make_dat();
    };
    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
un_average_weights(PyObject *self, PyObject *arg)
{
    
    Interface* interface;
    PyArg_ParseTuple(arg, "L", &interface);
    
    for(auto iter=interface->data->actions.begin();
            iter!=interface->data->actions.end();
            ++iter){
        iter->second->un_average();
    };
    Py_INCREF(Py_None);
    return Py_None;
};
static PyObject *
export_weights(PyObject *self, PyObject *arg)
{
    
    Interface* interface;
    PyArg_ParseTuple(arg, "L", &interface);
    
    
    PyObject * list=PyList_New(0);
    for(auto iter=interface->data->actions.begin();
            iter!=interface->data->actions.end();
            ++iter){
        //iter->second->average(step);
        PyObject * k=PyLong_FromLong(iter->first);
        PyObject * v=iter->second->to_py_dict();
        PyList_Append(
                list,
                PyTuple_Pack(2,
                    k,
                    v
                    )
                );
        Py_DECREF(k);
        Py_DECREF(v);
    };
    return list;
};
static PyObject *
set_raw(PyObject *self, PyObject *arg)
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
    Py_INCREF(Py_None);
    
    return Py_None;
};
static PyObject *
do_nothing(PyObject *self, PyObject *arg)
{
    Py_INCREF(Py_None);
    return Py_None;
};





};//end of isan
