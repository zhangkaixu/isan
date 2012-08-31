#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "dfa_beam_searcher.hpp"
#include "cws.hpp"
#include "isan/common/weights.hpp"
/**
 * g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3

 * */


class Python_Feature_Generator: public CWS_Feature_Generator{
public:
    PyObject * callback;
    Python_Feature_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Feature_Generator(){
        Py_DECREF(callback);
    };
    void operator()(State_Type& state, Feature_Vector& fv){
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


class Python_State_Generator: public CWS_State_Generator{
public:
    PyObject * callback;
    Python_State_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_State_Generator(){
        Py_DECREF(callback);
    };
    void operator()(State_Type& key, std::vector<std::pair<Action_Type, State_Type> > & nexts){
        PyObject * state=key.pack();
        PyObject * arglist=Py_BuildValue("(O)",state);
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);Py_CLEAR(arglist);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        PyObject * tmp_item;
        nexts.clear();
        for(int i=0;i<size;i++){
            tri=PySequence_GetItem(result,i);
            
            tmp_item=PySequence_GetItem(tri,0);
            Action_Type action=*PyUnicode_AS_UNICODE(tmp_item);
            Py_DECREF(tmp_item);

            tmp_item=PySequence_GetItem(tri,1);
            State_Type next_state(tmp_item);
            Py_DECREF(tmp_item);
            
            nexts.push_back(std::pair<Action_Type,State_Type>(action,next_state));
            Py_DECREF(tri);
        };
        Py_DECREF(result);
    };
};


//typedef Weights<Feature_String ,Score_Type> Default_Weights;
class Default_Weights : public Weights<Feature_String ,Score_Type>{
public:
    PyObject * to_py_dict(){
        PyObject * dict=PyDict_New();
        //
        for(auto it=map->begin();it!=map->end();++it){
            PyDict_SetItem(dict,PyBytes_FromStringAndSize(it->first.pt,it->first.length),PyLong_FromLong(it->second));
        };
        
        Py_INCREF(dict);
        return dict;
    };
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

inline void bytes_to_string(PyObject * bytes, Smart_String<char>& string){
    char* buffer;
    size_t length;
    PyBytes_AsStringAndSize(bytes,&buffer,(Py_ssize_t*)&(length));
    string=Feature_String(buffer,length);
};

inline void list_to_fv(PyObject * list, Feature_Vector & fv){
    fv.clear();
    long size=PySequence_Size(list);
    for(int i=0;i<size;i++){
        fv.push_back(Feature_String());
        PyObject * bytes=PySequence_GetItem(list,i);
        bytes_to_string(bytes,fv.back());
        Py_DECREF(bytes);
    };
    Py_DECREF(list);
};




/**
 * 负责： 与searcher沟通，生成 <state,action,score>
 * 需要：
 *      给一个原来的 state， 生成 fv 
 *      给一个原来的 state 生成 <new_state, action>
 *     fv与 action 生成 score，并 返回
 * */
class Searcher_Data : public DFA_Beam_Searcher_Data<State_Type,Action_Type,Score_Type> {
public:
    CWS_Feature_Generator * feature_generator;
    CWS_State_Generator * state_generator;
    
    Chinese* raw;
    std::map<Action_Type, Default_Weights* > actions;
    Searcher_Data(CWS_State_Generator *state_generator,CWS_Feature_Generator * feature_generator){
        this->feature_generator=feature_generator;
        this->state_generator=state_generator;
        raw=NULL;
    };
    void gen_next(State_Type& key,std::vector<std::pair<Action_Type,State_Type> >& nexts,
            std::vector<Score_Type>& scores){
        Feature_Vector fv;
        
        (*this->feature_generator)(key,fv);
        
        (*state_generator)(key,nexts);
        scores.resize(nexts.size());
        for(int i=0;i<nexts.size();i++){
            scores[i]=(*(this->actions[nexts[i].first]))(fv);
        };
    };
    
    ~Searcher_Data(){
        
    };
};



/**
 * The main interface between C and Python
 * */
class Interface{
public:
    State_Type init_key;
    PyObject *callback;
    Searcher_Data* searcher_data;
    DFA_Beam_Searcher<State_Type,Action_Type,Score_Type>* searcher;
    Chinese* raw;
    CWS_Feature_Generator * feature_generator;
    CWS_State_Generator * state_generator;
    
    
    Interface(State_Type init_key,int beam_width){
        feature_generator=new Default_Feature_Generator();
        state_generator=new Default_State_Generator();
        raw=NULL;
        searcher_data=new Searcher_Data(state_generator,feature_generator);
        
        this->init_key=init_key;
        searcher=new DFA_Beam_Searcher<State_Type,Action_Type,Score_Type>(searcher_data,beam_width);
    };
    void set_raw(Chinese& raw){
        if(this->raw)delete this->raw;
        this->raw=new Chinese(raw);
        this->searcher_data->raw=this->raw;
        this->feature_generator->set_raw(this->raw);
    }
    ~Interface(){
        delete feature_generator;
        delete state_generator;
        delete searcher_data;
        delete searcher;
    };
};





static PyObject *
search(PyObject *self, PyObject *arg)
{
    //std::cout<<"search begin\n";
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    Interface* interface=
            (Interface*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);

    
    tmp=PySequence_GetItem(arg,1);

    
    //std::cout<<"call searcher\n";
    std::vector<Action_Type> result;
    interface->searcher->call(interface->init_key,PyLong_AsLong(tmp),result);
    //std::cout<<"called searcher\n";
    Py_CLEAR(tmp);

    PyObject * list=PyList_New(result.size());
    
    for(int i=0;i<result.size();i++){
        unsigned int la=result[i];
        PyList_SetItem(list,i,PyUnicode_FromUnicode(&la,1));
    }
    //std::cout<<"searchend\n";
    return list;
};


static PyObject *
searcher_new(PyObject *self, PyObject *arg)
{
    
    PyObject * py_init_stat;
    
    int beam_width;
    PyObject * py_state_cb;
    PyObject * py_feature_cb;
    PyArg_ParseTuple(arg, "iOOO", &beam_width,&py_init_stat,&py_state_cb,&py_feature_cb);
    State_Type* init_key = NULL;
    if(py_init_stat!=Py_None){
        init_key = new State_Type(py_init_stat);
    }else{
        init_key = new Default_State_Type();
    };
    

    
    Interface* interface=new Interface(*init_key,beam_width);
    delete init_key;
    
    
    if(py_feature_cb!=Py_None){
        delete interface->feature_generator;
        interface->feature_generator=new Python_Feature_Generator(py_feature_cb);
        interface->searcher_data->feature_generator=interface->feature_generator;
    }else{
    };
    
    if(py_state_cb!=Py_None){
        delete interface->state_generator;
        interface->state_generator=new Python_State_Generator(py_state_cb);
        interface->searcher_data->state_generator=interface->state_generator;
    }else{
    };
    
    return PyLong_FromLong((long)interface);
};

static PyObject *
searcher_delete(PyObject *self, PyObject *arg){
    delete (Interface*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
};


static PyObject *
set_raw(PyObject *self, PyObject *arg)
{
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    Interface* interface=
            (Interface*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    PyObject *new_raw=PySequence_GetItem(arg,1);
    long raw_size=PySequence_Size(new_raw);
    
    Chinese raw(raw_size);
    for(int i=0;i<raw_size;i++){
        PyObject *tmp=PySequence_GetItem(new_raw,i);
        raw.pt[i]=(Chinese_Character)*PyUnicode_AS_UNICODE(tmp);
        Py_CLEAR(tmp);
    }
    interface->set_raw(raw);
    Py_CLEAR(new_raw);
    Py_INCREF(Py_None);
    
    return Py_None;
};

static PyObject *
set_action(PyObject *self, PyObject *arg)
{
    
    Interface* interface;
    int step;
    PyObject * py_action;
    PyObject * py_dict;
    PyArg_ParseTuple(arg, "IOO", &interface,&py_action,&py_dict);
    Action_Type action=*PyUnicode_AS_UNICODE(py_action);
    
    
    interface->searcher_data->actions[action]=new Default_Weights(py_dict);
    Py_INCREF(Py_None);
    return Py_None;
    
    
};

static PyObject *
update_action(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject * py_action;
    PyObject * py_state;
    long delta=0;
    long step=0;
    PyArg_ParseTuple(arg, "IOOii", &interface,&py_state,&py_action,&delta,&step);
    State_Type state(py_state);
    Action_Type action=(Action_Type)* PyUnicode_AS_UNICODE(py_action);
    
    Feature_Vector fv;
    (*(interface->feature_generator))(state,fv);
    
    
    (*(interface->searcher_data->actions[action])).update(fv,delta,step);
    
    Py_INCREF(Py_None);
    return Py_None;
};


static PyObject *
export_weights(PyObject *self, PyObject *arg)
{
    
    Interface* interface;
    int step;
    PyObject * py_action;
    PyArg_ParseTuple(arg, "IiO", &interface,&step,&py_action);
    
    Action_Type action=*PyUnicode_AS_UNICODE(py_action);
    //Py_DECREF(py_action);
    
    interface->searcher_data->actions[action]->average(step);
    return interface->searcher_data->actions[action]->to_py_dict();
    
    //return PyLong_FromLong((long)interface);
};

/** stuffs about the module def */
static PyMethodDef dfabeamMethods[] = {
    //{"system",  spam_system, METH_VARARGS,"Execute a shell command."},
    //{"add",  spam_add, METH_O,""},
    {"new",  searcher_new, METH_VARARGS,""},
    {"delete",  searcher_delete, METH_O,""},
    {"set_raw",  set_raw, METH_O,""},
    {"search",  search, METH_O,""},
    {"set_action",  set_action, METH_VARARGS,""},
    {"update_action",  update_action, METH_VARARGS,""},
    {"export_weights",  export_weights, METH_VARARGS,""},
    //{"test_map",  test_map, METH_O,""},
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