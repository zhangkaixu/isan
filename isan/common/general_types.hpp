#pragma once
#include <Python.h>
#include <string>
#include "isan/common/searcher.hpp"
#include "isan/common/smart_string.hpp"
namespace isan{
typedef long Action_Type;

typedef int Score_Type;

typedef Smart_Chars State_Type;

typedef Smart_Chars Feature_String;
typedef std::vector<Feature_String> Feature_Vector;


typedef unsigned short Chinese_Character;
typedef Smart_String<Chinese_Character> Chinese;


typedef Alpha<Action_Type,State_Type,Score_Type> Alpha_Type;
typedef State_Info<Alpha_Type> State_Info_Type;


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

};//end of isan
