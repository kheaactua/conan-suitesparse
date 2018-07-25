#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools
from conans.errors import ConanException


class SuiteSparseConan(ConanFile):
    """ Tested with versions 3.3.4 and 3.2.9 """

    name     = 'suitesparse'
    version  = '5.2.0'
    license  = 'AMD License: BSD 3-clause'
    url      = 'https://github.com/kheaactua/conan-suitesparse'
    md5_hash = '8e625539dbeed061cc62fbdfed9be7cf'

    # Not available for Windows
    settings = {
        'os':         ['Linux'],
        'arch':       ['x86_64', 'x86'],
        'build_type': ['Release', 'Debug'],
        'compiler':   ['gcc', 'clang']
    }

    def build_requirements(self):
        pack_names = None
        if tools.os_info.linux_distro == "ubuntu":
            pack_names = [
                'liblapack-dev', 'build-essential', 'libopenblas-dev'
            ]

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
        archive = 'SuiteSparse-%s.tar.gz'%self.version
        tools.download('http://faculty.cse.tamu.edu/davis/SuiteSparse/%s'%archive, archive)
        tools.unzip(archive)

        tools.check_md5(archive, self.md5_hash)

    def build(self):

        self.run('cd SuiteSparse && make -j %d'%tools.cpu_count())

    def package(self):
        self.copy(pattern='*',  dst='lib',      src=os.path.join('SuiteSparse', 'lib'),      excludes='.gitignore')
        self.copy(pattern='*',  dst='share',    src=os.path.join('SuiteSparse', 'share'),    excludes='.gitignore')
        self.copy(pattern='*',  dst='bin',      src=os.path.join('SuiteSparse', 'bin'),      excludes='.gitignore')
        self.copy(pattern='*',  dst='include/suitesparse', src=os.path.join('SuiteSparse', 'include'),  excludes='.gitignore')

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
