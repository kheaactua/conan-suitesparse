#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools, CMake, MSBuild

# The Windows portion was inspired by
# https://github.com/ComFreek/suitesparse-conan-pkg


class SuiteSparseConan(ConanFile):
    name        = 'suitesparse'
    version     = '5.1.2'
    license     = 'AMD License: BSD 3-clause'
    description = 'Suite of sparse matrix software.'
    url         = 'https://github.com/kheaactua/conan-suitesparse'
    generators  = 'cmake'
    requires    = (
        'helpers/[>=0.3]@ntc/stable',
    )

    settings = {'os': ['Windows'], 'compiler': None, 'build_type': None, 'arch': None}

    def source(self):
        self.run("git clone --depth 1 https://github.com/ComFreek/suitesparse-metis-for-windows.git suitesparse")
        self.run("cd suitesparse")

        # This small hack might be useful to guarantee proper /MT /MD linkage
        # in MSVC if the packaged project doesn't have variables to set it
        # properly
        tools.replace_in_file("suitesparse/CMakeLists.txt", "PROJECT(SuiteSparseProject)",
            '''PROJECT(SuiteSparseProject)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        cmake = CMake(self)
        cmake.configure(source_folder="suitesparse")

        msbuild = MSBuild(self)

        # Usually, MSBuild tries to guess the "configuration" and "platform"
        # (in Visual Studio Solution/Project terminology) to use for calling
        # msbuild.exe. E.g. an x86_64 release build will lead to
        # "configuration" = "Release" and "platform" = "x64", thus calling
        # msbuild.exe with:
        #   /p:Configuration=Debug /p:Platform="x64"
        #
        # However, the Visual Studio Solutions generated here (by CMake)
        # will have their platform named "Win32" in case of Conan's arch being
        # "x86".
        # => Rewrite the "guess mapping"
        msbuild.build("SuiteSparseProject.sln", platforms={'x86': 'Win32', 'x86_64': 'x64'})

        # Not calling the install target because without using CMake, I think
        # we'd need to hack the solution file to set the install path.

    def package(self):
        self.copy("**/*.lib", dst="lib", keep_path=False)
        self.copy("**/*.dll", dst="bin", keep_path=False)

        dest = os.path.join('include', 'suitesparse')
        self.copy(pattern='*.h',   dst=dest, keep_path=False)
        self.copy(pattern='*.hpp', dst=dest, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.bindirs = ['bin']
        # Some directories must be globally visible because
        # some files (e.g. umfpack/umfpack.h) try to include from
        # these without specifying a relative path.
        self.cpp_info.includedirs = ["include", "include/amd", "include/suitesparse"]

        # Add the DLLs to the RUNPATH
        self.env_info.path.append(os.path.join(self.package_folder, 'lapack_windows', 'x32' if 'x86' == self.settings.arch else 'win64'))

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
