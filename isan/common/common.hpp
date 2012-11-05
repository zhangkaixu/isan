#pragma once
#include <Python.h>
#include <vector>
#include <map>
#include "isan/common/smart_string.hpp"
#include "isan/common/general_types.hpp"

namespace isan{


class Feature_Generator{
public:
    const Chinese* raw;
    virtual void set_raw(const Chinese* raw){
        this->raw=raw;
    };
    virtual void operator()(const State_Type& key,Feature_Vector& fv)=0;
};

class State_Generator{
public:
    typedef Alpha_Type Alpha;
    typedef typename Alpha::State STATE;
    typedef typename Alpha::Action ACTION;
    Chinese* raw;
    STATE init_state;
    void set_raw(Chinese* raw){
        this->raw=raw;
    };
    inline virtual void operator()(
            const int& ind, STATE& key,
            std::vector<ACTION>& actions,
            std::vector<int>& next_inds,
            std::vector<STATE > & next_states){
        (*this)(key,actions,next_states);
        next_inds.clear();
        for(int i=0;i<actions.size();i++){
            next_inds.push_back(ind+1);
        };
    };
    virtual void operator()(STATE& key, std::vector<ACTION>&,std::vector<STATE > & nexts){};
};

class Reduced_State_Generator{
public:
    typedef Alpha_Type Alpha;
    typedef typename Alpha::State STATE;
    typedef typename Alpha::Action ACTION;
    Chinese* raw;
    STATE init_state;
    void set_raw(Chinese* raw){
        this->raw=raw;
    };
    virtual void operator()(
            const int,
            const STATE& key,
            const int,
            const STATE& key2, 
            std::vector<ACTION>&,
            std::vector<int>& next_inds,
            std::vector<STATE > & nexts)=0;
};

class Early_Stop_Checker{
public:
    typedef Alpha_Type Alpha;
    typedef typename Alpha::State STATE;
    typedef typename Alpha::Action ACTION;
    virtual bool operator()(
        const int step,
        const std::vector<Alpha*>& last_alphas,
        const std::vector<STATE>& states
            ){
        return false;
    };
};

class Python_Early_Stop_Checker : public Early_Stop_Checker{
public:
    PyObject * callback;
    Python_Early_Stop_Checker(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Early_Stop_Checker(){
        Py_DECREF(callback);
    };
    virtual bool operator()(
        const int step,
        const std::vector<Alpha*>& last_alphas,
        const std::vector<State_Type>& next_states
            ){
        PyObject * next_state_list=PyList_New(next_states.size());
        for(int i=0;i<next_states.size();i++){
            PyList_SetItem(next_state_list,i,
                next_states[i].pack()
            );
        };
        PyObject * move_list=PyList_New(next_states.size());
        for(int i=0;i<next_states.size();i++){
            PyList_SetItem(
                    move_list,
                    i,
                    pack_alpha(last_alphas[i])
                    );
        };

        PyObject * py_step=PyLong_FromLong(step);
        PyObject * arglist=PyTuple_Pack(3,
                py_step,
                next_state_list,
                move_list
                );
        PyObject * pfv= PyObject_CallObject(this->callback, arglist);

        Py_DECREF(py_step);
        Py_DECREF(move_list);
        Py_DECREF(next_state_list);
        Py_DECREF(arglist);

        bool rtn = (pfv==Py_True);
        Py_DECREF(pfv);
        return rtn;
    };

};

class Python_Feature_Generator: public Feature_Generator{
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
            fv.push_back(Feature_String((unsigned char*)buffer,length));
        };
        Py_DECREF(pfv);
    };
};


class Python_State_Generator: public State_Generator{
public:
    PyObject * callback;
    Python_State_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_State_Generator(){
        Py_DECREF(callback);
    };

    inline virtual void operator()(
            const int& ind,
            State_Type& key,
            std::vector<Action_Type>& next_actions,
            std::vector<int>& next_inds,
            std::vector<State_Type>& next_states)
    {
        PyObject * state=key.pack();
        PyObject * arglist=Py_BuildValue("(iO)",ind,state);
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);Py_CLEAR(arglist);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        next_actions.resize(size);
        next_states.clear();
        for(int i=0;i<size;i++){
            tri=PyList_GET_ITEM(result,i);
            if(PyTuple_GET_SIZE(tri)==2){
                next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
                next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,1)));
            }else{
                next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
                next_inds.push_back(PyLong_AsLong(PyTuple_GET_ITEM(tri,1)));
                next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,2)));
            };
        };
        Py_DECREF(result);
    };

};


class Python_Reduced_State_Generator: public Reduced_State_Generator{
public:
    PyObject * callback;
    Python_Reduced_State_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Reduced_State_Generator(){
        Py_DECREF(callback);
    };
    void operator()(
            const int ind1,
            const State_Type& key, 
            const int ind2,
            const State_Type& second_key,
            std::vector<Action_Type>&next_actions,
            std::vector<int>& next_inds,
            std::vector<State_Type> & next_states){
        PyObject * state=key.pack();
        PyObject * second_state=second_key.pack();

        PyObject * arglist=Py_BuildValue(
                "(iOiO)",
                ind1,
                state,
                ind2,
                second_state
                );
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);
        Py_CLEAR(second_state);
        Py_CLEAR(arglist);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        next_actions.resize(size);
        next_states.clear();
        next_inds.clear();
        for(int i=0;i<size;i++){
            tri=PyList_GET_ITEM(result,i);
            next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
            next_inds.push_back(PyLong_AsLong(PyTuple_GET_ITEM(tri,1)));
            next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,2)));
        };
        Py_DECREF(result);
    };
};


};//end of isan
