#pragma once
#include <vector>
#include <ext/hash_map>
#include <map>
#include <math.h>
#include "isan/common/common.hpp"
#include "isan/utls/dat.hpp"


namespace isan{

template<class KEY,class VALUE>
class Weights{
    typedef __gnu_cxx::hash_map<KEY,size_t,typename KEY::HASH> _Map2;
public:
    typedef __gnu_cxx::hash_map<KEY,VALUE,typename KEY::HASH> Map; //use hashmap as key-value map
    //typedef std::map<KEY,VALUE> Map;
    Map* map; //value map
    Map* acc_map; //acc map for average
    Map* backup; // used for average and unaverage
    _Map2* last_update;
    DATMaker* dat;
    VALUE _d;
    double _p;
    int penalty;

    Weights(){
        map=new Map();
        acc_map=new Map();
        last_update=new _Map2();
        backup=NULL;
        dat=NULL;

        _d=0.001;// decay for l1 regularization
        _p=0.999;
        penalty=1;

    };
    void set_penalty(int penalty,VALUE d=0){
        this->penalty=penalty;
        switch(penalty){
            case(0):
                break;
            case(1):
                _d=d; break;
            case(2):
                _p=d; break;
        };
    };
    ~Weights(){
        delete map;map=NULL;
        delete acc_map;acc_map=NULL;
        delete backup;backup=NULL;
        delete last_update;last_update=NULL;

    };
    void make_dat(){
        
        std::vector<std::pair<KEY, VALUE> > list;
        long checksum=0;
        for(auto iter=map->begin();iter!=map->end();++iter){
            list.push_back(std::pair<KEY,VALUE>(iter->first,iter->second));
            checksum+=iter->second;
            list.back().first.make_positive();
        }
        this->dat=new DATMaker();
        this->dat->make_dat(list);
        this->dat->shrink();
    };

    inline void no_penalty(const KEY& key,VALUE& value,const VALUE& delta,const size_t& d_step){
        (*acc_map)[key]+=value*d_step+delta;
        value+=delta;
    };
    inline void l1_penalty_full(const KEY& key,VALUE& value,const VALUE& delta,const size_t& d_step){
        VALUE& d=_d;
        VALUE d_value=d_step*d;
        VALUE new_value=(value>0?value:-value)-d_value;
        if(new_value<0)new_value=0;
        if(value<0) new_value*=-1;
        if (new_value==0 && new_value!=value){
            (*acc_map)[key]+=(value)*(value)/2/d-value+delta;
        }else{
            (*acc_map)[key]+=(value+new_value)*(d_step+1)/2-value+delta;
        };
        value=new_value+delta;
    };
    inline void l1_penalty(const KEY& key,VALUE& value,const VALUE& delta,const size_t& d_step){
        VALUE d_value=_d;
        VALUE new_value=(value>0?value:-value)-d_value;
        if(new_value<0)new_value=0;
        if(value<0) new_value*=-1;
        (*acc_map)[key]+=value*d_step+new_value-value+delta;
        value=new_value+delta;
    };

    inline void l2_penalty(const KEY& key,VALUE& value,const VALUE& delta,const size_t& d_step){
        VALUE new_value=value*_p;
        (*acc_map)[key]+=value*d_step+new_value-value+delta;
        value=new_value+delta;
    };

    inline VALUE refresh(const KEY& key,const int step,const VALUE delta=0){
        
        typename Map::iterator got;
        got=map->find(key);
        if (got==map->end()) return 0;
        
        size_t& last_step=last_update->find(key)->second;

        VALUE& value=got->second;

        if (step<=last_step){ //just add delta
            
            if (!delta) return value;
            value+=delta;
            (*acc_map)[key]+=delta;
            return value;
        }
        size_t d_step=step-last_step;

        /* regularization */
        switch(penalty){
            case 0 :
                no_penalty(key,value,delta,d_step);
                break;
            case 1 :
                l1_penalty(key,value,delta,d_step);
                break;
            case 2 :
                l2_penalty(key,value,delta,d_step);
                break;
        };
        

        last_step=step;
        return value;
    };
    
    //update
    void update(const std::vector<KEY>& fv,
            VALUE delta,
            int step){
        typename Map::iterator got;
        VALUE sd=step*delta;
        for(int i=0;i<fv.size();i++){
            const KEY& key=fv[i];
            got=map->find(key);
            if(got==map->end()){// new key, insert
                (*map)[key]=delta;
                (*last_update)[key]=step;
                if(acc_map)(*acc_map)[key]=sd;
            }else{ // exist key, update
                refresh(key,step,delta);
            };
        };
    };
    /* get the value of the keys */
    inline VALUE operator()(const std::vector<KEY>& fv,size_t step){
        VALUE value=0;
        if(this->dat){//if dat, use dat
            auto& tree=*this->dat;
            for(auto f=fv.begin();f!=fv.end();++f){
                value+=tree.get(*f);
            };
        }else{
            typename Map::const_iterator got;
            for(int i=0;i<fv.size();i++){// for every key=fv[i]
                value+=refresh(fv[i],step);
            };
        };
        return value;
    };
    /*
     * average the weights
     * */
    void average(int step){
        if(backup)delete backup;
        typename Map::iterator it;
        for(it=acc_map->begin();it!=acc_map->end();++it){
            const KEY& key=(*it).first;
            refresh(key,step);
        };
        this->backup=this->map;
        this->map=new Map();
        for(it=acc_map->begin();it!=acc_map->end();++it){
            const KEY& key=(*it).first;
            VALUE value=(*it).second;
            (*map)[key]=(VALUE)
                    (
                        (double)value/step*1000
                        +0.5
                    );
        };
        make_dat();
    };
    /*
     * unaverage
     * */
    void un_average(){
        delete map;
        map=backup;
        backup=NULL;
        delete dat;
        dat=NULL;
    };
};
class Default_Weights : public Weights<Feature_String ,Score_Type>{
public:
    PyObject * to_py_dict(){
        PyObject * dict=PyDict_New();
        for(auto it=map->begin();it!=map->end();++it){
            PyObject * key=it->first.pack();//PyBytes_FromStringAndSize((char*)it->first.pt,it->first.length);
            PyObject * value=PyLong_FromLong(it->second);
            PyDict_SetItem(dict,key,value);
            Py_DECREF(key);
            Py_DECREF(value);
        };
        return dict;
    };
    Default_Weights(){
        this->dat=NULL;
        backup=NULL;
    }
    Default_Weights(PyObject * dict){
        
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        
        char* buffer;
        size_t length;
        while (PyDict_Next(dict, &pos, &key, &value)) {
            PyBytes_AsStringAndSize(key,&buffer,(Py_ssize_t*)&(length));
            (*map)[Feature_String((Smart_Chars::Char*)buffer,length)]=PyLong_AsLong(value);
        };
    };
};

};//isan
