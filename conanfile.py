from conans import ConanFile, tools
from os import getenv
from random import getrandbits
from distutils.dir_util import copy_tree

class StormEngine(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "output_directory": "ANY",
        "watermark_file": "ANY",
        "crash_reports": [True, False],
        "steam": [True, False],
        "conan_sdl": [True, False]
    }
    
    requires = [
        "zlib/1.2.13",
        "spdlog/1.9.2",
        "fast_float/3.4.0",
        "mimalloc/2.0.3",
        "sentry-native/0.4.14"
    ]
    
    build_requires = "catch2/2.13.7"

    def requirements(self):
        if self.settings.os == "Windows":
            self.requires("7zip/19.00")
        else:
            self.requires("openssl/1.1.1n")
        self.options["libsndfile"].with_mpeg = False
        if self.options.conan_sdl:
            self.requires("sdl/2.0.18")

    generators = "cmake_multi"

    default_options = {
        "sentry-native:backend": "crashpad",
        "mimalloc:shared": True,
        "mimalloc:override": True
    }

    def imports(self):
        self._dest = str(self.options.output_directory) + "/" + getenv("CONAN_IMPORT_PATH", "bin")
        self._install_folder("/src/techniques", "/resource/techniques")
        self._install_folder("/src/libs/shared_headers/include/shared", "/resource/shared")
        if self.settings.os == "Windows":
            self._install_bin("crashpad_handler.exe")
            if self.options.crash_reports:
                self._install_bin("7za.exe")
            self._install_bin("mimalloc*.dll") 
        else:
            self._install_bin("crashpad_handler")
            if self.settings.build_type == "Debug":
                self._install_lib("libmimalloc-debug.so.2.0")
                self._install_lib("libmimalloc-debug.so")
            else:
                self._install_lib("libmimalloc.so.2.0")
                self._install_lib("libmimalloc.so")
        self._write_watermark()

    def _write_watermark(self):
        with open(str(self.options.watermark_file), 'w') as f:
            f.write("#pragma once\n#define STORM_BUILD_WATERMARK ")
            f.write(self._generate_watermark())
            f.write("\n")

    def _generate_watermark(self):
        git = tools.Git()
        try:
            if git.is_pristine():
                return "%s(%s)" % (git.get_branch(), git.get_revision())
            else:
                return "%s(%s)-DIRTY(%032x)" % (git.get_branch(), git.get_revision(), getrandbits(128))
        except:
            return "Unknown"

    def _install_bin(self, name):
        self.copy(name, dst=self._dest, src="bin")

    def _install_lib(self, name):
        self.copy(name, dst=self._dest, src="lib")

    def _install_folder(self, src, dst):
        copy_tree(self.recipe_folder + src, self._dest + dst)
