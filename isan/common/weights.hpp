#pragma once
#include <vector>
#include <ext/hash_map>
#include <map>
#include "isan/common/common.hpp"
#include "isan/utls/dat.hpp"


namespace isan{

template<class KEY,class VALUE>
class Weights{
public:
    typedef __gnu_cxx::hash_map<KEY,VALUE,typename KEY::HASH> Map;
    //typedef std::map<KEY,VALUE> Map;
    Map* map;
    Map* acc_map;
    Map* backup;
    DATMaker* dat;

    Weights(){
        map=new Map();
        acc_map=new Map();
        backup=NULL;
        dat=NULL;

    };
    ~Weights(){
        delete map;map=NULL;
        delete acc_map;acc_map=NULL;
        delete backup;backup=NULL;

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
    inline VALUE operator()(const std::vector<KEY>& fv)const{
        VALUE value=0;
        if(this->dat){
            auto& tree=*this->dat;
            for(auto f=fv.begin();f!=fv.end();++f){
                value+=tree.get(*f);
            };
        }else{
            typename Map::const_iterator got;
            for(int i=0;i<fv.size();i++){
                got = map->find(fv[i]);
                if(got!=map->end()){
                    value+=got->second;
                }
            };
        };
        return value;
    };
    void average(int step){
        if(backup)delete backup;
        this->backup=this->map;
        this->map=new Map();
        typename Map::iterator it;
        for(it=acc_map->begin();it!=acc_map->end();++it){
            const KEY& key=(*it).first;
            VALUE value=(*it).second;
            (*map)[key]=(VALUE)
                    (
                        (((double)(*backup)[key]-(double)value/step))*1000
                        +0.5
                    );
        };
        make_dat();
    };
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
            PyObject * key=PyBytes_FromStringAndSize((char*)it->first.pt,it->first.length);
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
            (*map)[Feature_String((unsigned char*)buffer,length)]=PyLong_AsLong(value);
        };
    };
};

};//isan
