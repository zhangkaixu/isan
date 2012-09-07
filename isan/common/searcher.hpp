#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <vector>


template <class ACTION, class STATE, class SCORE>
class Searcher_Data{
public:
    virtual void shift(
            STATE& state, 
            std::vector<ACTION>& actions,
            std::vector<STATE>& next_states,
            std::vector<SCORE>& scores
            )=0;
    virtual void reduce(
            const STATE& state, 
            const STATE& predictor,
            std::vector<ACTION>& actions,
            std::vector<STATE>& next_states,
            std::vector<SCORE>& scores
            ){return;};
};


template <class ACTION, class STATE, class SCORE>
class Searcher{
public:
    int beam_width;
    Searcher_Data<ACTION,STATE,SCORE>* data;

};
