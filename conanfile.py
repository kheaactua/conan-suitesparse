#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools, CMake, MSBuild
from conans.errors import ConanException

# The Windows portion was inspired by https://github.com/ComFreek/suitesparse-conan-pkg


class SuiteSparseConan(ConanFile):
    """ Tested with versions 3.3.4 and 3.2.9 """

    name        = 'suitesparse'
    version     = '5.2.0' # TODO windows version might be 5.1.2
    license     = 'AMD License: BSD 3-clause'
    description = "Suite of sparse matrix software.  Current windows install is actually 5.1.2, not 5.2.0!"
    url         = 'https://github.com/kheaactua/conan-suitesparse'
    settings    = 'os', 'compiler', 'build_type', 'arch'
    generators  = 'cmake'

    # Hash for Linux download
    md5_hash  = '8e625539dbeed061cc62fbdfed9be7cf'

    def build_requirements(self):
        pack_names = None
        if tools.os_info.linux_distro == "ubuntu":
            pack_names = ['liblapack-dev', 'build-essential', 'libopenblas-dev']

            if self.settings.arch == "x86":
                full_pack_names = []
                for pack_name in pack_names:
                    full_pack_names += [pack_name + ":i386"]
                pack_names = full_pack_names

        if pack_names:
            installer = tools.SystemPackageTool()
            try:
                installer.update() # Update the package database
                installer.install(" ".join(pack_names)) # Install the package
            except ConanException:
                self.output.warn('Could not run system updates to fetch build requirements.')

    def source(self):
        if 'Linux' == self.settings.os: self._source_linux()
        else: self._source_win()

    def _source_linux(self):
        archive = 'SuiteSparse-%s.tar.gz'%self.version

        from source_cache import copyFromCache
        if not copyFromCache(archive):
            tools.download('http://faculty.cse.tamu.edu/davis/SuiteSparse/%s'%archive, archive)
        tools.unzip(archive)

        tools.check_md5(archive, self.md5_hash)

    def _source_win(self):
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
        if 'Linux' == self.settings.os: self._build_linux()
        else: self._build_win()

    def _build_linux(self):
        self.run('cd SuiteSparse && make -j %d'%tools.cpu_count())

    def _build_win(self):
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
        if 'Linux' == self.settings.os: self._package_linux()
        else: self._package_win()

    def _package_linux(self):
        self.copy(pattern='*',  dst='lib',      src=os.path.join('SuiteSparse', 'lib'),      excludes='.gitignore')
        self.copy(pattern='*',  dst='share',    src=os.path.join('SuiteSparse', 'share'),    excludes='.gitignore')
        self.copy(pattern='*',  dst='bin',      src=os.path.join('SuiteSparse', 'bin'),      excludes='.gitignore')
        self.copy(pattern='*',  dst='include/suitesparse', src=os.path.join('SuiteSparse', 'include'),  excludes='.gitignore')

    def _package_win(self):
        self.copy("**/*.lib", dst="lib", keep_path=False)
        self.copy("**/*.dll", dst="bin", keep_path=False)

        dest = os.path.join('include', 'suitesparse')
        self.copy(pattern='*.h',   dst=dest, keep_path=False)
        self.copy(pattern='*.hpp', dst=dest, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        if 'Windows' == self.settings.os:
            # Some directories must be globally visible because
            # some files (e.g. umfpack/umfpack.h) try to include from
            # these without specifying a relative path.
            self.cpp_info.includedirs = ["include", "include/amd", "include/suitesparse"]
            # self.cpp_info.libs = ["suitesparseconfig.lib", "libumfpack"]

            # Add the DLLs to the RUNPATH
            self.env_info.path.append(os.path.join(self.package_folder, 'lapack_windows', 'x32' if 'x86' == self.settings.arch else 'win64'))
        elif 'Linux' == self.settings.os:
            self.env_info.LD_LIBRARY_PATH.append(os.path.join(self.package_folder, 'lib'))

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
