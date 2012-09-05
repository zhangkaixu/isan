#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/common.hpp"
#include "isan/common/weights.hpp"
#include "isan/parsing/push_down.hpp"

using namespace isan;


typedef Push_Down<Action_Type,State_Type,Score_Type> Python_Push_Down;
class Python_Push_Down_Data : public Push_Down_Data<Action_Type,State_Type,Score_Type>{
public:
    PyObject* shift_callback;
    PyObject* reduce_callback;
    General_Feature_Generator * feature_generator;
    std::map<Action_Type, Default_Weights* > actions;

    State_Type cached_state;
    std::map<Action_Type, Score_Type> cached_scores;
    Feature_Vector fv;

    Python_Push_Down_Data(PyObject* shift_callback,PyObject* reduce_callback,
            General_Feature_Generator* feature_generator){
        this->shift_callback=shift_callback;
        this->reduce_callback=reduce_callback;
        this->feature_generator=feature_generator;
        Py_INCREF(shift_callback);
        Py_INCREF(reduce_callback);
        cached_state=State_Type();
    };
    ~Python_Push_Down_Data(){
        Py_DECREF(shift_callback);
        Py_DECREF(reduce_callback);
        for(auto iter=actions.begin();
            iter!=actions.end();
            ++iter){
            delete iter->second;
        }
    };

    void shift(
            State_Type& state, 
            std::vector<Action_Type>& next_actions,
            std::vector<State_Type>& next_states,
            std::vector<Score_Type>& scores
            ){
        PyObject * py_state=state.pack();
        PyObject * arglist=Py_BuildValue("(O)",py_state);
        PyObject * result= PyObject_CallObject(this->shift_callback, arglist);
        Py_CLEAR(py_state);Py_CLEAR(arglist);

        if(!(cached_state==state)){
            (*feature_generator)(state,fv);
            cached_state=state;
            cached_scores.clear();
        }


        long size=PySequence_Size(result);
        PyObject * tri;
        PyObject * tmp_item;
        next_actions.resize(size);
        scores.resize(size);
        next_states.clear();
        for(int i=0;i<size;i++){
            tri=PySequence_GetItem(result,i);
            
            tmp_item=PySequence_GetItem(tri,0);
            next_actions[i]=(PyLong_AsUnsignedLong(tmp_item));
            auto action=next_actions[i];
            Py_DECREF(tmp_item);

            tmp_item=PySequence_GetItem(tri,1);
            next_states.push_back(State_Type(tmp_item));
            Py_DECREF(tmp_item);
            
            Py_DECREF(tri);
            
            auto got=actions.find(action);
            if(got==actions.end()){
                actions[action]=new Default_Weights();
            };
            scores[i]=(*actions[action])(fv);
        };
        Py_DECREF(result);
    };
    void reduce(
            const State_Type& state, 
            const State_Type& predictor,
            std::vector<Action_Type>& next_actions,
            std::vector<State_Type>& next_states,
            std::vector<Score_Type>& scores
            ){
        PyObject * py_state=state.pack();
        PyObject * py_predictor=predictor.pack();
        PyObject * arglist=Py_BuildValue("(OO)",py_state,py_predictor);
        PyObject * result= PyObject_CallObject(this->reduce_callback, arglist);
        Py_CLEAR(py_state);
        Py_CLEAR(py_predictor);Py_CLEAR(arglist);

        
        if(!(cached_state==state)){
            (*feature_generator)(state,fv);
            cached_state=state;
            cached_scores.clear();
        };



        long size=PySequence_Size(result);
        PyObject * tri;
        PyObject * tmp_item;
        next_actions.resize(size);
        scores.resize(size);
        next_states.clear();
        for(int i=0;i<size;i++){
            tri=PySequence_GetItem(result,i);
            
            tmp_item=PySequence_GetItem(tri,0);
            next_actions[i]=(PyLong_AsUnsignedLong(tmp_item));
            auto action=next_actions[i];
            Py_DECREF(tmp_item);

            tmp_item=PySequence_GetItem(tri,1);
            next_states.push_back(State_Type(tmp_item));
            Py_DECREF(tmp_item);
            
            Py_DECREF(tri);
            
            auto got=actions.find(action);
            if(got==actions.end()){
                actions[action]=new Default_Weights();
            };
            auto got2=cached_scores.find(action);
            if(got2!=cached_scores.end()){
                scores[i]=got2->second;
            }else{
                cached_scores[action]=scores[i]=(*actions[action])(fv);
            }
        };


        Py_DECREF(result);
    };
};




class Interface{
public:
    State_Type init_state;
    int beam_width;
    Python_Push_Down_Data * data;
    Python_Push_Down * push_down;
    Python_Feature_Generator* feature_generator;
    
    
    Interface(State_Type init_state,int beam_width,
            PyObject * py_shift_callback,
            PyObject * py_reduce_callback,
            PyObject * py_feature_cb
            ){
        this->init_state=init_state;
        this->beam_width=beam_width;
        feature_generator=new Python_Feature_Generator(py_feature_cb);
        this->data=new Python_Push_Down_Data(
                py_shift_callback,
                py_reduce_callback,
                feature_generator);
        this->push_down=new Python_Push_Down(this->data,beam_width);

    };
    void set_raw(){
    }
    ~Interface(){
        delete this->data;
        delete this->push_down;
        delete feature_generator;
    };
};




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
pushdown_delete(PyObject *self, PyObject *arg){
    delete (Interface*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
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

static PyObject *
set_action(PyObject *self, PyObject *arg)
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
update_action(PyObject *self, PyObject *arg)
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
call(PyObject *self, PyObject *arg){
    Interface* interface;
    Action_Type action;
    PyObject * list;
    PyArg_ParseTuple(arg, "LBO", &interface,&action,&list);

    auto& actions=interface->data->actions;
    auto got=actions.find(action);
    if(got==actions.end()){
        actions[action]=new Default_Weights();
    };
    
    Feature_Vector fv;
    
    long size=PySequence_Size(list);
    char* buffer;
    size_t length;
    for(int i=0;i<size;i++){
        PyObject * bytes=PySequence_GetItem(list,i);
        PyBytes_AsStringAndSize(bytes,&buffer,(Py_ssize_t*)&(length));
        fv.push_back(Feature_String(buffer,length));
        Py_DECREF(bytes);
    };
    long value=(*actions[action])(fv);

    return PyLong_FromLong(value);
};

/** stuffs about the module def */
static PyMethodDef pushdownMethods[] = {
    {"new",  pushdown_new, METH_VARARGS,""},
    {"delete",  pushdown_delete, METH_O,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  set_action, METH_VARARGS,""},
    {"update_action",  update_action, METH_VARARGS,""},
    {"call",  call, METH_VARARGS,""},
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


