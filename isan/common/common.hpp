#pragma once
#include <Python.h>
#include <vector>
#include <map>
#include "isan/common/smart_string.hpp"

namespace isan{

typedef unsigned char Action_Type;
class Smart_Chars: public Smart_String<unsigned char>{
public:
    PyObject* pack() const{
        return PyBytes_FromStringAndSize((char*)pt,length);
    };
    Smart_Chars(){
        //std::cout<<*_ref_count<<"\n";
    };
    Smart_Chars(PyObject* py_key){
        char* buffer;
        Py_ssize_t len;
        PyBytes_AsStringAndSize(py_key,&buffer,&len);
        length=(size_t)len;
        pt=new unsigned char[length];
        memcpy(pt,buffer,length*sizeof(unsigned char));        
    };
    Smart_Chars(unsigned long length){
        pt=new unsigned char[length];
        this->length=length;
    };
    Smart_Chars(unsigned char* buffer, Smart_Chars::SIZE_T length){
        pt=new unsigned char[length];
        this->length=length;
        memcpy(pt,buffer,length*sizeof(unsigned char));
        //for(int i=0;i<length;i++){
        //    if(!pt[i])pt[i]=120;
        //};
    };
    void make_positive(){
        for(int i=0;i<length;i++){
            if(pt[i]==0){
                std::cout<<"zero\n";
            };
        };
    };
    inline unsigned char& operator[](const int i) const{
        return pt[i];
    };
};
typedef int Score_Type;
typedef Smart_Chars State_Type;
typedef Smart_Chars Feature_String;
typedef std::vector<Feature_String> Feature_Vector;

typedef unsigned short Chinese_Character;
typedef Smart_String<Chinese_Character> Chinese;

template <class RAW, class STATE, class FEATURE_VECTOR>
class Feature_Generator{
public:
    const RAW* raw;
    virtual void set_raw(const RAW* raw){
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

template <class STATE, class ACTION>
class Early_Stop_Checker{
public:
    virtual bool operator()(
        int step,
        const std::vector<STATE>& last_states,
        const std::vector<ACTION>& actions,
        const std::vector<STATE>& states
            ){
        return false;
    };
};


typedef Feature_Generator<Chinese,State_Type,Feature_Vector> General_Feature_Generator;
typedef State_Generator<Chinese,State_Type,Action_Type> General_State_Generator;
typedef Reduced_State_Generator<Chinese,State_Type,Action_Type> General_Reduced_State_Generator;
typedef Early_Stop_Checker<State_Type,Action_Type> General_Early_Stop_Checker;

class Python_Early_Stop_Checker : public General_Early_Stop_Checker{
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
        int step,
        const std::vector<State_Type>& last_states,
        const std::vector<Action_Type>& actions,
        const std::vector<State_Type>& next_states
            ){
        PyObject * last_state_list=PyList_New(last_states.size());
        for(int i=0;i<last_states.size();i++){
            PyList_SetItem(last_state_list,i,
                last_states[i].pack()
            );
        };
        PyObject * action_list=PyList_New(next_states.size());
        for(int i=0;i<next_states.size();i++){
            PyList_SetItem(action_list,i,
                PyLong_FromLong(actions[i])
            );
        };
        PyObject * next_state_list=PyList_New(next_states.size());
        for(int i=0;i<next_states.size();i++){
            PyList_SetItem(next_state_list,i,
                next_states[i].pack()
            );
        };

        PyObject * py_step=PyLong_FromLong(step);
        PyObject * arglist=PyTuple_Pack(4,py_step,last_state_list,action_list,next_state_list);
        PyObject * pfv= PyObject_CallObject(this->callback, arglist);

        //for(int i=0;i<next_states.size();i++){
        //    Py_DECREF(PyList_GET_ITEM(last_state_list,i));
            //PyList_GET_ITEM(last_state_list,i);
        //};
        //std::cout<<"haha\n";
        Py_DECREF(py_step);
        Py_DECREF(last_state_list);
        Py_DECREF(action_list);
        Py_DECREF(next_state_list);
        Py_DECREF(arglist);

        bool rtn = (pfv==Py_True);
        Py_DECREF(pfv);
        return rtn;

    };

};

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
            fv.push_back(Feature_String((unsigned char*)buffer,length));
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
