#pragma once

#include "isan/common/common.hpp"
#include "isan/common/searcher.hpp"



/**
 * searcher data
 * provide information for searcher
 * */

namespace isan{



class General_Searcher_Data : 
        public Searcher_Data<Alpha_Type>{
public:

    Feature_Generator * feature_generator;
    State_Generator * shifted_state_generator;
    Reduced_State_Generator * reduced_state_generator;
    Early_Stop_Checker * early_stop_checker;

    size_t learning_step;

    // init this object
    General_Searcher_Data(
            Early_Stop_Checker * early_stop_checker,
            State_Generator *shifted_state_generator,
            Reduced_State_Generator *reduced_state_generator,
            Feature_Generator* feature_generator){
        this->early_stop_checker=early_stop_checker;
        if(this->early_stop_checker)this->use_early_stop=true;
        this->feature_generator=feature_generator;
        this->shifted_state_generator=shifted_state_generator;
        
        this->reduced_state_generator=reduced_state_generator;
        //std::cout<<reduced_state_generator<<"\n";
        learning_step=0;
    };
    ~General_Searcher_Data(){
    };

    virtual bool early_stop(
            int step,
            const std::vector<Alpha_Type*>& last_alphas,
            const std::vector<State_Type>& states
            ){
        return (*early_stop_checker)(
                step,
                last_alphas,
                states);
    };

    inline void shift(
            const int& ind,
            State_Type& state, 
            std::vector<Action_Type>& next_actions,
            std::vector<int>& next_inds,
            std::vector<State_Type>& next_states,
            std::vector<Score_Type>& scores
            ){
        next_inds.clear();// clear the vector first
        (*shifted_state_generator)(ind,state,next_actions,next_inds,next_states);
        
        cal_weights(state,next_actions,scores,learning_step);
    };
    void reduce(
            const int state_ind,
            const State_Type& state, 
            const std::vector<Alpha_Type*>& pred_alphas,
            std::vector<Action_Type>& next_actions,
            std::vector<int>& next_inds,
            std::vector<State_Type>& next_states,
            std::vector<int>& reduce_pred_alphas,
            std::vector<Score_Type>& scores
            ){
        if(this->reduced_state_generator){
            (*reduced_state_generator)(
                    state_ind,
                    state,
                    pred_alphas,
                    next_actions,
                    next_inds,
                    next_states,
                    reduce_pred_alphas
                    );
            cal_weights(state,next_actions,scores,learning_step);
        }
    };

    // calculate the sum of the weights according to the list of symbolic features
    inline void cal_weights(
            const STATE& state,
            const std::vector<ACTION>& next_actions,
            std::vector<SCORE>& scores,
            size_t step
            ){
        scores.resize(next_actions.size());
        for(int i=0;i<next_actions.size();i++){
            scores[i]=0;
        };
        
        (*feature_generator)(state,next_actions,0,0,scores);
    };
};

/**
 * interface of the whole model
 * */
class Interface{
    typedef Searcher<State_Info_Type > My_Searcher;
public:
    State_Type init_state;
    int beam_width;
    General_Searcher_Data * data;

    My_Searcher * push_down;
    
    State_Generator * shifted_state_generator;
    Reduced_State_Generator * reduced_state_generator;
    Feature_Generator * feature_generator;
    Early_Stop_Checker * early_stop_checker;
    
    Chinese* raw;
    
    Interface(int beam_width,
            PyObject * py_early_stop_callback,
            PyObject * py_shift_callback,
            PyObject * py_reduce_callback,
            PyObject * py_feature_cb
            ){
        if(PyLong_Check(py_shift_callback)){
            shifted_state_generator=(State_Generator *) PyLong_AsUnsignedLong(py_shift_callback);
        }else{
            shifted_state_generator=new Python_State_Generator(py_shift_callback);
        };

        reduced_state_generator=NULL;
        if(py_reduce_callback!=Py_None){
            reduced_state_generator=new Python_Reduced_State_Generator(py_reduce_callback);
        };

        if(PyLong_Check( py_feature_cb)){
            feature_generator=(Feature_Generator*) PyLong_AsUnsignedLong( py_feature_cb);
        }else{
            feature_generator=new Python_Feature_Generator( py_feature_cb);
        };
        early_stop_checker=NULL;
        if(py_early_stop_callback!=Py_None){
            early_stop_checker=new Python_Early_Stop_Checker(py_early_stop_callback);
        }

        raw=NULL;
        this->beam_width=beam_width;
        this->data=new General_Searcher_Data(
                early_stop_checker,
                shifted_state_generator,
                reduced_state_generator,
                feature_generator);
        this->push_down=new My_Searcher(this->data,beam_width);

    };
    
    void set_raw(Chinese& raw){
        if(this->raw)delete this->raw;
        this->raw=new Chinese(raw);
        this->shifted_state_generator->raw=this->raw;
        this->feature_generator->set_raw(this->raw);
    }

    ~Interface(){
        delete this->data;
        delete this->push_down;
        delete feature_generator;
        delete shifted_state_generator;
        delete early_stop_checker;
        if(reduced_state_generator)
            delete reduced_state_generator;
    };
};

};//isan
