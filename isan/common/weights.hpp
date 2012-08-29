#pragma once
#include <vector>
#include <ext/hash_map>
#include <map>
#include "isan/common/common.hpp"

template<class KEY,class VALUE>
class Weights{
public:
    typedef __gnu_cxx::hash_map<KEY,VALUE,typename KEY::HASH> Map;
    //typedef std::map<KEY,VALUE> Map;
    Map* map;
    Map* acc_map;

    Weights(){
        map=new Map();
        acc_map=new Map();
    };
    ~Weights(){
        delete map;
        delete acc_map;
    };
    
    void update(const std::vector<KEY>& fv,
            VALUE delta,
            int step){
        typename Map::iterator got;
        VALUE sd=step*delta;
        for(int i=0;i<fv.size();i++){
            const KEY& key=fv[i];
            got=map->find(key);
            if(got==map->end()){
                (*map)[key]=delta;
                if(acc_map)(*acc_map)[key]=sd;
            }else{
                got->second+=delta;
                if(acc_map)(*acc_map)[key]+=sd;
            };
        };
    };
    VALUE operator()(const std::vector<KEY>& fv){
        VALUE value=0;
        //int miss=0;
        typename Map::const_iterator got;
        for(int i=0;i<fv.size();i++){
            got = map->find(fv[i]);
            if(got!=map->end()){
                value+=got->second;
            }else{
                
            }
            //if(map->count(fv[i]))value+=(*map)[fv[i]];
        };
        return value;
    };
    void average(int step){
        typename Map::iterator it;
        //std::cout<<step<<"\n";
        for(it=acc_map->begin();it!=acc_map->end();++it){
            const KEY& key=(*it).first;
            VALUE value=(*it).second;
            //std::cout<<(*map)[key]<<" "<<(*acc_map)[key]<<" ";
            (*map)[key]=(VALUE)
                    (
                        ((double)((*map)[key]-value/step))*1000
                        +0.5
                    );
            //std::cout<<(*map)[key]<<"\n";
        };
    };
};
