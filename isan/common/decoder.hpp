#pragma once

#include "isan/common/common.hpp"
#include "isan/common/weights.hpp"
#include "isan/common/searcher.hpp"

namespace isan{


class General_Searcher_Data : public Searcher_Data<Action_Type,State_Type,Score_Type>{
public:

    General_Feature_Generator * feature_generator;
    General_State_Generator * shifted_state_generator;
    General_Reduced_State_Generator * reduced_state_generator;

    std::map<Action_Type, Default_Weights* > actions;

    //cache for FV
    State_Type cached_state;
    std::map<Action_Type, Score_Type> cached_scores;
    Feature_Vector fv;

    General_Searcher_Data(
            General_State_Generator *shifted_state_generator,
            General_Feature_Generator * feature_generator){
        this->feature_generator=feature_generator;
        this->shifted_state_generator=shifted_state_generator;
        this->reduced_state_generator=NULL;
        cached_state=State_Type();
    };
    General_Searcher_Data(
            General_State_Generator *shifted_state_generator,
            General_Reduced_State_Generator *reduced_state_generator,
            General_Feature_Generator* feature_generator){
        this->shifted_state_generator=shifted_state_generator;
        this->reduced_state_generator=reduced_state_generator;
        this->feature_generator=feature_generator;
        cached_state=State_Type();
    };
    ~General_Searcher_Data(){
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
        if(!(cached_state==state)){
            (*feature_generator)(state,fv);
            cached_state=state;
            cached_scores.clear();
        }
        (*shifted_state_generator)(state,next_actions,next_states);
        scores.resize(next_actions.size());
        for(int i=0;i<next_actions.size();i++){
            auto action=next_actions[i];
            auto got=actions.find(action);
            if(got==actions.end()){
                actions[action]=new Default_Weights();
            };
            scores[i]=(*actions[action])(fv);
        };
    };
    void reduce(
            const State_Type& state, 
            const State_Type& predictor,
            std::vector<Action_Type>& next_actions,
            std::vector<State_Type>& next_states,
            std::vector<Score_Type>& scores
            ){
        if(!(cached_state==state)){
            (*feature_generator)(state,fv);
            cached_state=state;
            cached_scores.clear();
        };
        (*reduced_state_generator)(state,predictor,next_actions,next_states);
        scores.resize(next_actions.size());
        for(int i=0;i<next_actions.size();i++){
            auto action=next_actions[i];
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
    };
};

template<template <class a,class b,class c> class STATE_INFO>
class General_Interface{
    typedef Searcher<Action_Type,State_Type,Score_Type,STATE_INFO> My_Searcher;
public:
    State_Type init_state;
    int beam_width;
    General_Searcher_Data * data;

    My_Searcher * push_down;
    
    General_State_Generator * shifted_state_generator;
    General_Reduced_State_Generator * reduced_state_generator;
    General_Feature_Generator * feature_generator;
    
    Chinese* raw;
    
    General_Interface(State_Type init_state,int beam_width,
            PyObject * py_shift_callback,
            PyObject * py_reduce_callback,
            PyObject * py_feature_cb
            ){
        shifted_state_generator=new Python_State_Generator(py_shift_callback);
        reduced_state_generator=new Python_Reduced_State_Generator(py_reduce_callback);
        feature_generator=new Python_Feature_Generator(py_feature_cb);

        this->init_state=init_state;
        this->beam_width=beam_width;
        this->data=new General_Searcher_Data(
                shifted_state_generator,
                reduced_state_generator,
                feature_generator);
        this->push_down=new My_Searcher(this->data,beam_width);

    };
    General_Interface(State_Type init_state,int beam_width,
            PyObject * py_shift_callback,
            PyObject * py_feature_cb
            ){
        shifted_state_generator=new Python_State_Generator(py_shift_callback);
        reduced_state_generator=NULL;
        feature_generator=new Python_Feature_Generator(py_feature_cb);
        raw=NULL;
        this->data=new General_Searcher_Data(
                shifted_state_generator,
                feature_generator);

        this->init_state=init_state;
        this->beam_width=beam_width;
        this->push_down=new My_Searcher(this->data,beam_width);

    };
    General_Interface(State_Type init_state,int beam_width,
            General_State_Generator * shift_gen,
            General_Feature_Generator* feature_gen
            ){
        shifted_state_generator=shift_gen;
        reduced_state_generator=NULL;
        feature_generator=feature_gen;
        raw=NULL;
        this->data=new General_Searcher_Data(
                shifted_state_generator,
                feature_generator);

        this->init_state=init_state;
        this->beam_width=beam_width;
        this->push_down=new My_Searcher(this->data,beam_width);

    };
    void set_raw(Chinese& raw){
        if(this->raw)delete this->raw;
        this->raw=new Chinese(raw);
    }
    ~General_Interface(){
        delete this->data;
        delete this->push_down;
        delete feature_generator;
        delete shifted_state_generator;
        if(reduced_state_generator)
            delete reduced_state_generator;
    };
};

};//isan
