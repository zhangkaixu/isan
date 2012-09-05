#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/common.hpp"
#include "isan/common/weights.hpp"
#include "isan/parsing/push_down.hpp"

namespace isan{

typedef Smart_String<Chinese_Character> Chinese;
typedef Smart_String<char> Feature_String;
typedef std::vector<Feature_String> Feature_Vector;
class State_Type: public Smart_String<char>{
public:
    PyObject* pack() const{
        return PyBytes_FromStringAndSize(pt,length);
    };
    State_Type(){
    };
    State_Type(PyObject* py_key){
        char* buffer;
        Py_ssize_t len;
        int rtn=PyBytes_AsStringAndSize(py_key,&buffer,&len);
        length=(size_t)len;
        pt=new char[length];
        memcpy(pt,buffer,length*sizeof(char));        
    };
};
class Default_Weights : public Weights<Feature_String ,Score_Type>{
public:
    PyObject * to_py_dict(){
        PyObject * dict=PyDict_New();
        //
        for(auto it=map->begin();it!=map->end();++it){
            PyObject * key=PyBytes_FromStringAndSize(it->first.pt,it->first.length);
            PyObject * value=PyLong_FromLong(it->second);
            PyDict_SetItem(dict,key,value);
            Py_DECREF(key);
            Py_DECREF(value);
        };
        
        return dict;
    };
    Default_Weights(){
    }
    Default_Weights(PyObject * dict){
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        
        char* buffer;
        size_t length;
        while (PyDict_Next(dict, &pos, &key, &value)) {
            PyBytes_AsStringAndSize(key,&buffer,(Py_ssize_t*)&(length));
            (*map)[Feature_String(buffer,length)]=PyLong_AsLong(value);
        };
    };
};


/**
 * */

typedef Feature_Generator<Chinese,State_Type,Feature_Vector> Parser_Feature_Generator;
typedef State_Generator<Chinese,State_Type,Action_Type> CWS_State_Generator;


class Python_Feature_Generator: public Parser_Feature_Generator{
public:
    PyObject * callback;
    Python_Feature_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Feature_Generator(){
        Py_DECREF(callback);
    };
    void operator()(const State_Type& state, Feature_Vector& fv){
        PyObject * pkey=state.pack();
        PyObject * arglist=Py_BuildValue("(O)",pkey);
        
        PyObject * pfv= PyObject_CallObject(this->callback, arglist);
        
        Py_DECREF(pkey);
        Py_DECREF(arglist);
        
        fv.clear();
        char* buffer;
        size_t length;
        long size=PySequence_Size(pfv);
        PyObject * pf;
        for(int i=0;i<size;i++){
            pf=PySequence_GetItem(pfv,i);
            PyBytes_AsStringAndSize(pf,&buffer,(Py_ssize_t*)&(length));
            fv.push_back(Feature_String(buffer,length));
            Py_DECREF(pf);
        };
        Py_DECREF(pfv);
    };
};








typedef Push_Down<Action_Type,State_Type,Score_Type> Python_Push_Down;
class Python_Push_Down_Data : public Push_Down_Data<Action_Type,State_Type,Score_Type>{
public:
    PyObject* shift_callback;
    PyObject* reduce_callback;
    Parser_Feature_Generator * feature_generator;
    std::map<Action_Type, Default_Weights* > actions;

    Python_Push_Down_Data(PyObject* shift_callback,PyObject* reduce_callback,
            Parser_Feature_Generator* feature_generator){
        this->shift_callback=shift_callback;
        this->reduce_callback=reduce_callback;
        this->feature_generator=feature_generator;
        Py_INCREF(shift_callback);
        Py_INCREF(reduce_callback);
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

        Feature_Vector fv;
        (*feature_generator)(state,fv);
        //std::cout<<fv.size()<<"\n";


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

        
        Feature_Vector fv;
        (*feature_generator)(state,fv);
        //std::cout<<fv.size()<<"\n";


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


};//end of isan
