#pragma once
#include "isan/common/smart_string.hpp"
namespace isan{
typedef unsigned char Action_Type;
class Smart_Chars: public Smart_String<unsigned char>{
public:
    PyObject* pack() const{
        return PyBytes_FromStringAndSize((char*)pt,length);
    };
    Smart_Chars(){
        //std::cout<<*_ref_count<<"\n";
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
