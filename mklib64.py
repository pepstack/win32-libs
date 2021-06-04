#!/usr/bin/python
# filename: mklib64.py
#   -- Make 64bits windows module files from MinGW x64 .dll
# author: cheungmine@qq.com
# date: 2017-03-14
#  vc100
# note: run in MSYS
#######################################################################
import os, sys, platform

import optparse, ConfigParser

APPFILE = os.path.realpath(sys.argv[0])
APPNAME,_ = os.path.splitext(os.path.basename(APPFILE))
APPVER = "1.0"
APPHELP = "Make 64bits windows module files from MinGW .dll"

#######################################
# check if file exists
def file_exists(file):
    if file and os.path.isfile(file) and os.access(file, os.R_OK):
        return True
    else:
        return False


#######################################
# check system is msys or cmd
def check_system():
    # platform.uname():
    print " * platform:", platform.platform()
    print " * version:", platform.version()
    print " * architecture:", platform.architecture()
    print " * machine:", platform.machine()
    print " * network node:", platform.node()
    print " * processor:", platform.processor()
    if platform.architecture() != ('32bit', 'WindowsPE'):
        sys.exit("[ERROR] Platform not support.")


#######################################
# get MSVC path environment
# C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC
def search_vspath():
    #for msvc in [150, 140, 130, 120, 110, 100, 90, 80, 70, 60]:
    for msvc in [100, 90, 80, 70, 60]:
        vsenv = "VS%dCOMNTOOLS" % msvc
        vspath = os.getenv(vsenv)

        if vspath:
            vcbat = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(vspath))), "VC\\vcvarsall.bat")
            if file_exists(vcbat):
                vspath = os.path.dirname(vcbat)
                print " * %s='%s'" % (vsenv, vspath)
                return vspath
    sys.exit("[ERROR] vcvarsall.bat not found")


#######################################
# check dll file
def validate_args(dll_file, out_path):
    if out_path:
        if not os.path.exists(out_path):
            sys.exit("[ERROR] Specified out path not exists: %s" % out_path)
        if not os.path.isdir(out_path):
            sys.exit("[ERROR] Specified out path not dir: %s" % out_path)
    else:
        out_path = os.path.dirname(APPFILE)

    dllbases = []
    titles = []

    if file_exists(dll_file):
        dllpath = os.path.dirname(dll_file)
        dllbase = os.path.basename(dll_file)
        title, ext = os.path.splitext(dllbase)
        if ext.lower() != ".dll":
            sys.exit("[ERROR] Not a .dll file: %r" % dll_file)

        return (dllpath, [dllbase], [title], out_path)
    elif os.path.isdir(dll_file):
        for f in os.listdir(dll_file):
            pf = os.path.join(dll_file, f)
            if file_exists(pf):
                dllbase = os.path.basename(pf)
                title, ext = os.path.splitext(dllbase)
                if ext.lower() == ".dll":
                    dllbases.append(dllbase)
                    titles.append(title)
        if not len(dllbases):
            sys.exit("[ERROR] dll files not found in given path: %s" % dll_file)
        else:
            return (dll_file, dllbases, titles, out_path)
    else:
        sys.exit("[ERROR] Either file is missing or is not readable: %s" % dll_file)


#######################################
def check_results(out_path, title):
    out_files = []

    def_file = os.path.join(out_path, title + ".def")
    if not file_exists(def_file):
        print "[ERROR] file not exists: %s" % def_file
    else:
        out_files.append(def_file)

    lib_file = os.path.join(out_path, title + ".lib")
    if not file_exists(lib_file):
        print "[ERROR] file not exists: %s" % lib_file
    else:
        out_files.append(lib_file)

    exp_file = os.path.join(out_path, title + ".exp")
    if not file_exists(exp_file):
        print "[ERROR] file not exists: %s" % exp_file
    else:
        out_files.append(exp_file)

    return out_files


###########################################################
# Usage for MSYS:
#   python mklib64.py -I "C:\DEVPACK\MinGW\msys\1.0\local\win64\bin" -O "./win64"
#
if __name__ == "__main__":
    print "*" * 54
    print "* %-50s *" % (APPNAME + " version: " + APPVER)
    print "* %-50s *" % APPHELP
    print "*" * 54

    if len(sys.argv) == 1:
        sys.exit("[ERROR] Input dll file not specified.")
    
    parser = optparse.OptionParser(usage='python %prog [options]', version="%prog " + APPVER)

    parser.add_option("-v", "--verbose",
        action="store_true", dest="verbose", default=True,
        help="be verbose (this is the default).")

    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose",
        help="quiet (no output).")

    group = optparse.OptionGroup(parser, APPNAME, APPHELP)

    parser.add_option_group(group)

    group.add_option("-I", "--dll-file",
        action="store", dest="dll_file", default=None,
        help="Specify input .dll file or path to export")

    group.add_option("-O", "--out-path",
        action="store", dest="out_path", default=None,
        help="Specify path for output files")

    (opts, args) = parser.parse_args()

    check_system()

    vspath = search_vspath()

    (dllpath, dllbases, titles, out_path) = validate_args(opts.dll_file, os.path.realpath(opts.out_path))

    print " * Input files:", dllpath
    for dll in dllbases:
        print " *             :", dll
    print " * Output path:", out_path

    out_dict = {}
    for i in range(0, len(dllbases)):
        print "-"*50
        dllbase = dllbases[i]
        title = titles[i]
        dll_file = os.path.join(dllpath, dllbase)

        print " * Make windows module definition: %s.def" % title
        msyscmd = 'pexports "%s" -o > "%s.def"' % (dll_file, os.path.join(out_path, title))
        ret = os.system(msyscmd)
        if ret != 0:
            sys.exit("[ERROR] MSYS command: %s" % msyscmd)

        print " * Make windows module import file: %s.lib" % title
        libcmd = 'cd "%s"&vcvarsall.bat x86_amd64&cd "%s"&lib /def:%s.def /machine:amd64 /out:%s.lib' % (vspath, out_path, title, title)
        ret = os.system(libcmd)
        if ret != 0:
            sys.exit("[ERROR] lib command: %s" % libcmd)

        out_dict[title] = check_results(out_path, title)

    print "=============== Output Files Report ==============="
    for title, files in out_dict.items():
        print "%s.dll =>" % title
        
        for f in files:
            print " * ", os.path.basename(f)
