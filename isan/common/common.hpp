#pragma once
#include <vector>
#include <map>

typedef unsigned short Chinese_Character;
typedef char Action_Type;
typedef int Score_Type;


template<class CHAR>
class String{
public:
    CHAR* pt;
    size_t length;
    String(){
        pt=NULL;
        this->length=0;
    };
    String(size_t length){
        pt=new CHAR[length];
        this->length=length;
    };
    String(const String& other){
        length=other.length;
        pt=new CHAR[length];
        memcpy(pt,other.pt,length*sizeof(CHAR));
    };
    String(char* buffer, size_t length){
        pt=new CHAR[length];
        this->length=length;
        memcpy(pt,buffer,length*sizeof(CHAR));
    };
    ~String(){
        if(pt)
            delete[] pt;
    };
    
    bool operator==(const String &next) const{
        if(length!=next.length)
            return false;
        for(int i=0;i<length;i++){
            if(pt[i]!=next.pt[i])return false;
        }
        return true;
    };
    bool operator<(const String& next)const{
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
        size_t operator()(const String& cx) const{
            size_t value=0;
            for(int i=0;i<cx.length;i++){
                if(i%4==0){
                    value+=cx.pt[i];
                }else if(i%4==1){
                    value+=cx.pt[i]<<8;
                }else if(i%4==2){
                    value+=cx.pt[i]<<16;
                }else{
                    value+=cx.pt[i]<<24;
                };
            }
            return value;
        }
    };
};

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
