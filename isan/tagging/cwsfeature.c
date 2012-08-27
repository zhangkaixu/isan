#include <Python.h>
#include <iostream>
#include <vector>

/**
 * g++ cwsfeature.c -I /usr/include/python3.2mu -shared -o cwsfeature.so -fPIC -O3

 * */

typedef unsigned short chinese_character;

PyObject * raw;
size_t raw_size;
std::vector<chinese_character> raw_vector;
PyObject* NAC=PyLong_FromLong(0);


struct Triple{
    char a;
    chinese_character b;
    char c;
};
struct Four{
    char a;
    chinese_character b;
    chinese_character c;
    char d;
};

static PyObject *
cwsfeature_set_raw(PyObject *self, PyObject *new_raw)
{
    raw=new_raw;
    raw_size=PySequence_Size(raw);
    raw_vector.clear();
    for(int i=0;i<raw_size;i++){
        raw_vector.push_back((chinese_character)*PyUnicode_AS_UNICODE(PySequence_GetItem(raw,i)));
    }
    
    Py_INCREF(Py_None);
    
    return Py_None;
};

static PyObject *
get_features(PyObject *self, PyObject *span)
{
    long ind=PyLong_AsLong(PySequence_GetItem(span,0));
    chinese_character left_action=(chinese_character)*PyUnicode_AS_UNICODE(PySequence_GetItem(span,1));
    chinese_character left_left_action=(chinese_character)*PyUnicode_AS_UNICODE(PySequence_GetItem(span,2));
    long sep_ind=PyLong_AsLong(PySequence_GetItem(span,3));

    chinese_character char_mid=ind-1>=0?raw_vector[ind-1]:-1;
    chinese_character char_right=ind<raw_size?raw_vector[ind]:-1;
    chinese_character char_left=ind-2>=0?raw_vector[ind-2]:-1;
    chinese_character char_left2=ind-3>=0?raw_vector[ind-3]:-1;
    chinese_character char_right2=ind+1<raw_size?raw_vector[ind+1]:-1;
    
    
    Triple f_trans={0,(left_action),(left_left_action)};

    Triple f_mid={1,(char_mid),(left_action)};
    Triple f_right={2,(char_right),(left_action)};
    Triple f_left={3,(char_left),(left_action)};
    
    Four f_mid_right={4,(char_mid),(char_right),(left_action)};
    Four f_left_mid={5,(char_left),(char_mid),(left_action)};
    Four f_left2_left={6,(char_left2),(char_left),(left_action)};
    Four f_right_right2={7,(char_right),(char_right2),(left_action)};
    

    PyObject* list=PyList_New(8);
    PyList_SetItem(list,0,PyBytes_FromStringAndSize((char*)&f_trans,sizeof(f_trans)));
    PyList_SetItem(list,1,PyBytes_FromStringAndSize((char*)&f_mid,sizeof(f_mid)));
    PyList_SetItem(list,2,PyBytes_FromStringAndSize((char*)&f_right,sizeof(f_right)));
    PyList_SetItem(list,3,PyBytes_FromStringAndSize((char*)&f_left,sizeof(f_left)));
    PyList_SetItem(list,4,PyBytes_FromStringAndSize((char*)&f_mid_right,sizeof(f_mid_right)));
    PyList_SetItem(list,5,PyBytes_FromStringAndSize((char*)&f_left_mid,sizeof(f_left_mid)));
    PyList_SetItem(list,6,PyBytes_FromStringAndSize((char*)&f_left2_left,sizeof(f_left2_left)));
    PyList_SetItem(list,7,PyBytes_FromStringAndSize((char*)&f_right_right2,sizeof(f_right_right2)));
    //PyList_SetItem(list,8,PyTuple_Pack(2,PyLong_FromLong(8),PySequence_GetSlice(raw,ind-sep_ind,ind)));
    return list;
};

static PyMethodDef cwsfeatureMethods[] = {
    //{"system",  spam_system, METH_VARARGS,"Execute a shell command."},
    //{"add",  spam_add, METH_O,""},
    {"set_raw",  cwsfeature_set_raw, METH_O,""},
    {"get_features",  get_features, METH_O,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef cwsfeaturemodule = {
   PyModuleDef_HEAD_INIT,
   "cwsfeature",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   cwsfeatureMethods
};

PyMODINIT_FUNC
PyInit_cwsfeature(void)
{
    return PyModule_Create(&cwsfeaturemodule);
}
