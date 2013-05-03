from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

ext_modules = [Extension("default_dep0", ["default_dep0.pyx"])]

ext_modules = cythonize("default_dep0.pyx",language='c++')

setup(
          name = 'task',
            cmdclass = {'build_ext': build_ext},
              ext_modules = ext_modules,
              )
