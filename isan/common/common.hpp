#pragma once
#include <Python.h>
#include <vector>
#include <map>
#include "isan/common/smart_string.hpp"

namespace isan{

typedef unsigned char Action_Type;
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
        PyBytes_AsStringAndSize(py_key,&buffer,&len);
        length=(size_t)len;
        pt=new char[length];
        memcpy(pt,buffer,length*sizeof(char));        
    };
};
typedef int Score_Type;
typedef Smart_String<char> Feature_String;
typedef std::vector<Feature_String> Feature_Vector;

typedef unsigned short Chinese_Character;
typedef Smart_String<Chinese_Character> Chinese;

template <class RAW, class STATE, class FEATURE_VECTOR>
class Feature_Generator{
public:
    RAW* raw;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(const STATE& key, FEATURE_VECTOR& fv)=0;
};

template <class RAW, class STATE, class ACTION>
class State_Generator{
public:
    RAW* raw;
    STATE init_state;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(STATE& key, std::vector<ACTION>&,std::vector<STATE > & nexts)=0;
};

template <class RAW, class STATE, class ACTION>
class Reduced_State_Generator{
public:
    RAW* raw;
    STATE init_state;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(const STATE& key,const STATE& key2, std::vector<ACTION>&,std::vector<STATE > & nexts)=0;
};



typedef Feature_Generator<Chinese,State_Type,Feature_Vector> General_Feature_Generator;
typedef State_Generator<Chinese,State_Type,Action_Type> General_State_Generator;
typedef Reduced_State_Generator<Chinese,State_Type,Action_Type> General_Reduced_State_Generator;
class Python_Feature_Generator: public General_Feature_Generator{
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
        PyObject * arglist=PyTuple_Pack(1,pkey);
        PyObject * pfv= PyObject_CallObject(this->callback, arglist);
        Py_DECREF(pkey);
        Py_DECREF(arglist);
        
        fv.clear();
        char* buffer;
        size_t length;
        long size=PySequence_Size(pfv);
        for(int i=0;i<size;i++){
            PyBytes_AsStringAndSize(PyList_GET_ITEM(pfv,i),&buffer,(Py_ssize_t*)&(length));
            fv.push_back(Feature_String(buffer,length));
        };
        Py_DECREF(pfv);
    };
};


class Python_State_Generator: public General_State_Generator{
public:
    PyObject * callback;
    Python_State_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_State_Generator(){
        Py_DECREF(callback);
    };
    void operator()(State_Type& key, std::vector<Action_Type>&next_actions,std::vector<State_Type> & next_states){
        PyObject * state=key.pack();
        PyObject * arglist=Py_BuildValue("(O)",state);
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);Py_CLEAR(arglist);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        next_actions.resize(size);
        next_states.clear();
        for(int i=0;i<size;i++){
            tri=PyList_GET_ITEM(result,i);
            next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
            next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,1)));
        };
        Py_DECREF(result);
    };
};


class Python_Reduced_State_Generator: public General_Reduced_State_Generator{
public:
    PyObject * callback;
    Python_Reduced_State_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Reduced_State_Generator(){
        Py_DECREF(callback);
    };
    void operator()(const State_Type& key, const State_Type& second_key,std::vector<Action_Type>&next_actions,std::vector<State_Type> & next_states){
        PyObject * state=key.pack();
        PyObject * second_state=second_key.pack();

        PyObject * arglist=Py_BuildValue("(OO)",state,second_state);
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);
        Py_CLEAR(second_state);
        Py_CLEAR(arglist);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        next_actions.resize(size);
        next_states.clear();
        for(int i=0;i<size;i++){
            tri=PyList_GET_ITEM(result,i);
            next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
            next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,1)));
        };
        Py_DECREF(result);
    };
};


};//end of isan
