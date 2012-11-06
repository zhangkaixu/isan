#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/searcher.hpp"
#include "isan/common/general_types.hpp"
#include "isan/common/weights.hpp"
#include "isan/common/decoder.hpp"
#include "isan/common/python_interface.hpp"
using namespace isan;

static struct PyModuleDef dfabeammodule = {
   PyModuleDef_HEAD_INIT,
   "dfabeam",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   interfaceMethods
};

PyMODINIT_FUNC
PyInit_dfabeam(void)
{
    return PyModule_Create(&dfabeammodule);
}
