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
public:
    std::string str;
    PyObject* pack() const{
        return PyBytes_FromStringAndSize((char*)str.data(),str.length());
    };
    Smart_Chars(){
    };
    ~Smart_Chars(){
    };
    Smart_Chars(const Smart_Chars& other){
        str=other.str;
    };
    Smart_Chars(PyObject* py_key){
        char* buffer;
        Py_ssize_t len;
        PyBytes_AsStringAndSize(py_key,&buffer,&len);
        str=std::string(buffer,len);
    };
    Smart_Chars(Char* buffer, Smart_Chars::SIZE_T length){
        str=std::string((char*)buffer,length);
    };
    Smart_Chars(const Smart_Chars& other,int length){
        str=std::string(other.str.data(),length);
    };
    inline void operator=(const Smart_Chars& other){
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
    };
    inline const size_t size() const{
        return str.length();
    };
    class HASH{
    public:
        inline SIZE_T operator()(const Smart_Chars& cx) const{
            SIZE_T value=0;
            for(int i=0;i<cx.str.length();i++){
                value+=(Char)cx.str[i]<<((i%8)*8);
            }
            return value;
        }
    };
    inline bool operator==(const Smart_Chars&next) const{
        return this->str==next.str;
    };
    inline bool operator<(const Smart_Chars& next)const{
        return -this->str.compare(next.str);
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
