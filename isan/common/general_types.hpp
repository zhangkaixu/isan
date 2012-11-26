#pragma once
#include <Python.h>
#include <string>
#include "isan/common/searcher.hpp"
#include "isan/common/smart_string.hpp"
namespace isan{
typedef long Action_Type;

class Smart_Chars{
public:
    typedef size_t SIZE_T;
    typedef unsigned char Char;
private:
    SIZE_T* _ref_count;
    SIZE_T length;
    Char* pt;
public:
    std::string str;
    PyObject* pack() const{
        return PyBytes_FromStringAndSize((char*)pt,length);
    };
    Smart_Chars(){
        pt=NULL;
        length=0;
        _ref_count=new SIZE_T();
        *_ref_count=1;
    };
    ~Smart_Chars(){
        (*_ref_count)--;
        if(!*_ref_count){
            delete _ref_count;
            if(pt)delete[] pt;
        }
    };
    Smart_Chars(const Smart_Chars& other){
        str=other.str;
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
    };
    Smart_Chars(PyObject* py_key){
        char* buffer;
        Py_ssize_t len;
        PyBytes_AsStringAndSize(py_key,&buffer,&len);
        str=std::string(buffer,len);
        length=(size_t)len;
        pt=new Char[length];
        memcpy(pt,buffer,length*sizeof(Char));        
        _ref_count=new SIZE_T();
        *_ref_count=1;
    };
    Smart_Chars(Char* buffer, Smart_Chars::SIZE_T length){
        pt=new Char[length];
        this->length=length;
        str=std::string((char*)buffer,length);
        _ref_count=new SIZE_T();
        *_ref_count=1;
    };
    Smart_Chars(const Smart_Chars& other,int length){
        pt=new Char[length];
        this->length=length;
        str=std::string(other.str.data(),length);
        _ref_count=new SIZE_T();
        *_ref_count=1;
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
        str=other.str;
    };
    void make_positive(){
        for(int i=0;i<str.length();i++){
            if(str[i]==0){
                std::cout<<"zero\n";
            };
        };
    };
    inline const Char operator[](const int i) const{
        return (Char)str[i];
        /*
        if((Char)str[i]!=pt[i]){
            std::cout<<(int)str[i]<<"\n";
            std::cout<<(int)pt[i]<<"\n";
            
            
            assert(false);
        };
        return pt[i];
        */
    };
    inline const size_t size() const{
        return str.length();
        /*
        if(length != str.length()){
            std::cout<<length<<"\n";
            std::cout<<str.length()<<"\n";
            assert(false);
        };
        return length;
        */
    };
    class HASH{
    public:
        inline SIZE_T operator()(const Smart_Chars& cx) const{
            SIZE_T value=0;
            for(int i=0;i<cx.str.length();i++){
                value+=cx.str[i]<<((i%8)*8);
            }
            return value;
        }
    };
    inline bool operator==(const Smart_Chars&next) const{
        return this->str==next.str;
        /*
        if(length!=next.length)
            return false;
        if(pt==next.pt)return true;
        for(int i=0;i<length;i++){
            if(pt[i]!=next.pt[i])return false;
        }
        return true;
        */
    };
    inline bool operator<(const Smart_Chars& next)const{
        if(str.length()<next.str.length())return 1;
        if(str.length()>next.str.length())return 0;
        for(int i=0;i<str.length();i++){
            if((Char)str[i]<(Char)next.str[i])return 1;
            if((Char)str[i]>(Char)next.str[i])return 0;
        }
        return 0;
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
