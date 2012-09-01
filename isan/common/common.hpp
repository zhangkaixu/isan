#pragma once
#include <vector>
#include <map>

typedef unsigned short Chinese_Character;
typedef int Score_Type;


template<class ITEM>
class Smart_String{
public:
    ITEM* pt;
    size_t length;
    size_t* _ref_count;
    Smart_String(){
        pt=NULL;
        length=0;
        _ref_count=new size_t[1];
        *_ref_count=1;
    };
    Smart_String(ITEM* buffer, size_t length){
        _ref_count=new size_t[1];
        *_ref_count=1;
        pt=new ITEM[length];
        this->length=length;
        memcpy(pt,buffer,length*sizeof(ITEM));
    };
    Smart_String(size_t length){
        _ref_count=new size_t[1];
        *_ref_count=1;
        pt=new ITEM[length];
        this->length=length;
    };
    Smart_String(const Smart_String& other){
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
    };
    void operator=(const Smart_String& other){
        (*_ref_count)--;
        if(!*_ref_count){
            delete[] _ref_count;
            if(pt)delete[] pt;
        }
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
    };
    ~Smart_String(){
        (*_ref_count)--;
        if(!*_ref_count){
            delete[] _ref_count;
            if(pt)delete[] pt;
        }
    };

    inline bool operator==(const Smart_String &next) const{
        if(length!=next.length)
            return false;
        for(int i=0;i<length;i++){
            if(pt[i]!=next.pt[i])return false;
        }
        return true;
    };
    bool operator<(const Smart_String& next)const{
        if(length<next.length)return 1;
        if(length>next.length)return 0;
        for(int i=0;i<length;i++){
            if(pt[i]<next.pt[i])return 1;
            if(pt[i]>next.pt[i])return 0;
        }
        return 0;
    };
    class HASH{
    public:
        inline size_t operator()(const Smart_String& cx) const{
            size_t value=0;
            for(int i=0;i<cx.length;i++){
                value+=cx.pt[i]<<((i%8)*8);
            }
            return value;
        }
    };
};

typedef unsigned char Action_Type;

template <class RAW, class STATE, class FEATURE_VECTOR>
class Feature_Generator{
public:
    RAW* raw;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(STATE& key, FEATURE_VECTOR& fv)=0;
};

template <class RAW, class STATE, class ACTION>
class State_Generator{
public:
    RAW* raw;
    STATE init_state;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(STATE& key, std::vector<std::pair<ACTION, STATE> > & nexts)=0;

};
