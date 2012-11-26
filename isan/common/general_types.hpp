#pragma once
#include <Python.h>
#include "isan/common/searcher.hpp"
#include "isan/common/smart_string.hpp"
namespace isan{
typedef long Action_Type;

template<class ITEM>
class Smart_String2{
public:
    typedef size_t SIZE_T;
    ITEM* pt;
    SIZE_T length;
    SIZE_T* _ref_count;
    Smart_String2(){
        pt=NULL;
        length=0;
        _ref_count=new SIZE_T();
        *_ref_count=1;
    };


};

class Smart_Chars: public Smart_String2<unsigned char>{
public:
    PyObject* pack() const{
        return PyBytes_FromStringAndSize((char*)pt,length);
    };
    Smart_Chars(){
        pt=NULL;
        length=0;
        _ref_count=new SIZE_T();
        *_ref_count=1;
        //std::cout<<*_ref_count<<"\n";
    };
    ~Smart_Chars(){
        (*_ref_count)--;
        if(!*_ref_count){
            delete _ref_count;
            if(pt)delete[] pt;
        }
    };
    Smart_Chars(const Smart_Chars& other){
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
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
    class HASH{
    public:
        inline SIZE_T operator()(const Smart_String2& cx) const{
            SIZE_T value=0;
            for(int i=0;i<cx.length;i++){
                value+=cx.pt[i]<<((i%8)*8);
            }
            return value;
        }
    };
    inline const size_t& size() const{
        return length;
    };
    inline bool operator==(const Smart_Chars&next) const{
        if(length!=next.length)
            return false;
        if(pt==next.pt)return true;
        for(int i=0;i<length;i++){
            if(pt[i]!=next.pt[i])return false;
        }
        return true;
    };
    inline bool operator<(const Smart_Chars& next)const{
        if(length<next.length)return 1;
        if(length>next.length)return 0;
        for(int i=0;i<length;i++){
            if(pt[i]<next.pt[i])return 1;
            if(pt[i]>next.pt[i])return 0;
        }
        return 0;
    };
    inline void operator=(const Smart_Chars& other){
        (*_ref_count)--;
        if(!*_ref_count){
            delete _ref_count;
            if(pt)delete[] pt;
        }
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
    };
};
typedef int Score_Type;
typedef Smart_Chars State_Type;
typedef Smart_Chars Feature_String;
typedef std::vector<Feature_String> Feature_Vector;

typedef unsigned short Chinese_Character;
typedef Smart_String<Chinese_Character> Chinese;

template<class Alpha>
inline static PyObject *
pack_alpha(Alpha alpha){
    PyObject * py_step=PyLong_FromLong(alpha->ind1);
    PyObject * py_state=alpha->state1.pack();
    PyObject * py_action=PyLong_FromLong(alpha->action);
    PyObject * py_move=PyTuple_Pack(3,py_step,py_state,py_action);
    Py_DECREF( py_step);
    Py_DECREF( py_state);
    Py_DECREF( py_action);
    return py_move;

};

typedef Alpha<Action_Type,State_Type,Score_Type> Alpha_Type;
typedef State_Info<Alpha_Type> State_Info_Type;

};
