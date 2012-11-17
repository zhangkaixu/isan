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
    virtual void operator()(
            const State_Type& key,
            const std::vector<Action_Type>& action,
            std::vector<Feature_Vector>& fv)
        =0;
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
            const std::vector<Alpha_Type*>&,
            std::vector<ACTION>&,
            std::vector<int>& next_inds,
            std::vector<STATE > & nexts,
            std::vector<int>& reduce_pred_alphas
            )=0;
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
    void operator()(
            const State_Type& state, 
            const std::vector<Action_Type>& actions,
            std::vector<Feature_Vector>& fvs){

        PyObject * p_action_list=PyList_New(actions.size());
        for(int i=0;i<actions.size();i++){
            PyList_SetItem(p_action_list,i,
                    PyLong_FromLong(actions[i]));
        }

        PyObject * pkey=state.pack();
        PyObject * arglist=PyTuple_Pack(2,pkey, p_action_list);
        PyObject * pfvs= PyObject_CallObject(this->callback, arglist);
        Py_DECREF(pkey);
        Py_DECREF(arglist);
        Py_DECREF( p_action_list);
        
        fvs.clear();
        char* buffer;
        size_t length;
        long size=PySequence_Size(pfvs);
        for(int i=0;i<size;i++){
            PyObject * pfv=PyList_GET_ITEM(pfvs,i);
            long fv_size=PySequence_Size(pfv);
            fvs.push_back(Feature_Vector());
            auto& fv=fvs.back();
            for(int j=0;j<fv_size;j++){
                PyBytes_AsStringAndSize(PyList_GET_ITEM(pfv,j),&buffer,(Py_ssize_t*)&(length));
                fv.push_back(Feature_String((unsigned char*)buffer,length));
            }
        };
        Py_DECREF(pfvs);
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
            next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
            next_inds.push_back(PyLong_AsLong(PyTuple_GET_ITEM(tri,1)));
            next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,2)));
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
            const std::vector<Alpha_Type*>& pred_alphas,
            std::vector<Action_Type>&next_actions,
            std::vector<int>& next_inds,
            std::vector<State_Type> & next_states,
            std::vector<int>& reduce_pred_alphas
            ){
        PyObject * state=key.pack();

        PyObject * pred_ind_list=PyList_New(pred_alphas.size());
        for(int i=0;i<pred_alphas.size();i++){
            PyList_SetItem(pred_ind_list,i,
                    PyLong_FromLong(pred_alphas[i]->ind1));
        }
        PyObject * pred_state_list=PyList_New(pred_alphas.size());
        for(int i=0;i<pred_alphas.size();i++){
            PyList_SetItem(pred_state_list,i,
                    pred_alphas[i]->state1.pack());
        }
        
        PyObject * arglist=Py_BuildValue(
                "(iOOO)",
                ind1,
                state,
                pred_ind_list,
                pred_state_list
                );
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);
        Py_CLEAR(arglist);
        Py_CLEAR(pred_ind_list);
        Py_CLEAR(pred_state_list);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        next_actions.resize(size);
        next_states.clear();
        next_inds.clear();
        reduce_pred_alphas.clear();
        for(int i=0;i<size;i++){
            tri=PyList_GET_ITEM(result,i);
            next_actions[i]=(PyLong_AsLong(PyTuple_GET_ITEM(tri,0)));
            next_inds.push_back(PyLong_AsLong(PyTuple_GET_ITEM(tri,1)));
            next_states.push_back(State_Type(PyTuple_GET_ITEM(tri,2)));
            reduce_pred_alphas.push_back(PyLong_AsLong(PyTuple_GET_ITEM(tri,3)));
        };
        Py_DECREF(result);
    };
};


};//end of isan
