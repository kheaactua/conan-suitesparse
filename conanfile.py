#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools, CMake, MSBuild
from conans.errors import ConanException


class SuiteSparseConan(ConanFile):
    name        = 'suitesparse'
    version     = '5.2.0'
    license     = 'AMD License: BSD 3-clause'
    description = 'Suite of sparse matrix software.'
    url         = 'https://github.com/kheaactua/conan-suitesparse'
    settings    = 'os', 'compiler', 'build_type', 'arch'
    generators  = 'cmake'
    md5_hash  = '8e625539dbeed061cc62fbdfed9be7cf'
    requires    = (
        'helpers/[>=0.3]@ntc/stable',
    )
    options     = {
        'blas': ['openblas', 'system'], # System basically doesn't do anything which should search system paths
    }
    default_options = (
        'blas=system'
    )

    settings = {'os': ['Linux']}


    def build_requirements(self):
        pack_names = None
        if tools.os_info.linux_distro == "ubuntu":
            pack_names = ['liblapack-dev', 'build-essential']
            if 'system' == self.options.blas:
                # Note: openblas doesn't exist on tegra.
                pack_names.append('libopenblas-dev')
                pack_names.append('libblas-dev')

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

    def requirements(self):
        if 'openblas' == self.options.blas:
            self.requires('openblas/[>=0.2.20]@ntc/stable')

    def source(self):
        archive = 'SuiteSparse-%s.tar.gz'%self.version

        from source_cache import copyFromCache
        if not copyFromCache(archive):
            tools.download('http://faculty.cse.tamu.edu/davis/SuiteSparse/%s'%archive, archive)
        tools.check_md5(archive, self.md5_hash)

        tools.unzip(archive)

        if 'openblas' in self.deps_cpp_info.deps:
            # LDFLAGS isn't used prevasively enough, so we need to hack the Makefile.
            tools.replace_in_file(
                file_path='SuiteSparse/SuiteSparse_config/SuiteSparse_config.mk',
                search='BLAS = -lopenblas',
                replace='BLAS = -L%s -lopenblas'%(self.deps_cpp_info['openblas'].rootpath + '/lib'),
            )

    def build(self):
        env_vars = {}

        if 'openblas' in self.deps_cpp_info.deps:
            env_vars['LDFLAGS']         = '-L%s/lib'%self.deps_cpp_info['openblas'].rootpath,
            env_vars['LD_LIBRARY_PATH'] = '%s/lib'%self.deps_cpp_info['openblas'].rootpath,

        with tools.environment_append(env_vars):
            self.run('cd SuiteSparse && make -j %d'%tools.cpu_count())

    def package(self):
        if 'Linux' == self.settings.os: self._package_linux()
        else: self._package_win()

    def _package_linux(self):
        self.copy(pattern='*',  dst='lib',      src=os.path.join('SuiteSparse', 'lib'),      excludes='.gitignore')
        self.copy(pattern='*',  dst='share',    src=os.path.join('SuiteSparse', 'share'),    excludes='.gitignore')
        self.copy(pattern='*',  dst='bin',      src=os.path.join('SuiteSparse', 'bin'),      excludes='.gitignore')
        self.copy(pattern='*',  dst='include/suitesparse', src=os.path.join('SuiteSparse', 'include'),  excludes='.gitignore')

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.env_info.LD_LIBRARY_PATH.append(os.path.join(self.package_folder, 'lib'))

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
