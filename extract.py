#!/usr/bin/env python3

"""
Extract all compressed files in a Minecraft world directory.

python3 {this_py_file} [<world_path>] [<target_path>] [--force]

world_path      If omitted (1st unnamed arg), use
                current directory.
                
target_path     If omitted (2nd unnamed arg), use (create)
                "/extracted/" under current directory.
                If specified, the directory must exist.

--force         Delete target_path if exists!
                (If force is not provided, using an existing non-empty path will cause the program to fail.)

If you get a large negative number as an error return on Windows, you are
probably using the builtin (quiet) copy of Python included with Windows.
Instead, install Python from python.org using the "All Users" and
"Add to PATH" options.
"""

import os 

import sys
import platform
import shutil
import gzip
ignore = [sys.argv[0], "extract.py", "README.md", "CHANGELOG.md"]
ignore_paths = []
    
def count_sub_paths(path):
    # See algrice' answer on <https://stackoverflow.com/questions/
    # 49284015/how-to-check-if-folder-is-empty-with-python>
    results = [f for f in os.listdir(path) if not f.startswith('.')]
    # sys.stderr.write("{} results in {}".format(len(results), path))
    return len(results)

def is_empty(path):
    count_sub_paths(path) == 0
total = 0
def extract(src, dst, level=0):
    # sys.stdout.write(" "*level + "(IN {})\n".format(dst))
    global total
    for sub in os.listdir(src):
        if sub.startswith("."):
            continue
        if sub in ignore:
            continue
        # print("Trying {}...".format(src))
        src_sub = os.path.join(src, sub)
        if src_sub.lower() in ignore_paths:
            continue
        dst_sub = os.path.join(dst, sub)
        
        if os.path.isdir(src_sub):
            # sys.stderr.write(" "*level + "{}/".format(sub))
            # sys.stdout.write(" ({})".format(dst_sub))
            # sys.stdout.write("\n")
            extract(src_sub, dst_sub, level+2)
        else:
            sys.stderr.write(" "*level + "{}".format(sub))
            try:
                # See <https://stackoverflow.com/questions
                # /31028815/how-to-unzip-gz-file-using-python>
                with gzip.open(src_sub, 'rb') as f_in:
                    if not os.path.isdir(dst):
                        os.makedirs(dst)
                    # else:
                    #     sys.stderr.write("{} is present"
                    #                      "...".format(dst))
                    with open(dst_sub, 'wb') as f_out:
                        # os.mkdir(dst_sub)
                        # sys.stderr.write("new directory name"
                        #                  " is from gz filename.")
                        shutil.copyfileobj(f_in, f_out)
                        sys.stderr.write(": extracted")
                        # total += count_sub_paths(dst_sub)
                        total += 1
            except gzip.BadGzipFile:
                sys.stderr.write(": SKIPPED non-gz file.")
                if is_empty(dst):
                    os.rmdir(dst)
                if os.path.exists(dst_sub):
                    os.remove(dst_sub)
            sys.stderr.write("\n")

def main():
    world_path = "."
    target_name = "extracted"
    ignore.append(target_name)
    dest_path = "."
    profile = None
    AppData = None
    print("Running...")
    if platform.system() == "Windows":
        profile = os.environ.get("USERPROFILE")
        AppData = os.environ.get("APPDATA")
    else:
        profile = os.environ.get("HOME")
        AppData = profile
    dot_minecraft = os.path.join(AppData, ".minecraft")
    settings = {}
    name = None
    sequential_args = ["world_path", "target_path"]
    seq_arg_i = 0
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith("--"):
            start = 2
            if name is not None:
                settings[name] = True
                name = None
            sign_i = arg.find("=")
            if sign_i > start:
                settings[arg[start:sign_i]] = arg[sign_i+1]
            else:
                name = arg[start:]
        else:
            if name is not None:
                settings[name] = arg
            else:
                if seq_arg_i < len(sequential_args):
                    name = sequential_args[seq_arg_i]
                    settings[name] = arg
                    seq_arg_i += 1
                    name = None
    if name is not None:
        settings[name] = True
        name = None
    if settings.get("world_path") is None:
        print("* You didn't specify a world"
              "name or world path as the parameter.")
        settings["world_path"] = os.getcwd()
        print("  * Trying current directory:"
              " '{}'".format(settings["world_path"]))
    else:
        if not os.path.isdir(settings["world_path"]):
            try_path = os.path.join(settings["world_path"])
            if os.path.isdir(try_path):
                settings["world_path"] = try_path
    good_flag = "level.dat"
    good_flag_path = os.path.join(settings["world_path"], good_flag)
    if not os.path.isfile(good_flag_path):
        raise ValueError("* The '{}' is not present, so the world"
                         " path does not seem to be a Minecraft world:"
                         " '{}'".format(good_flag,
                                        settings["world_path"]))
    if settings.get("target_path") is None:
        settings["target_path"] = os.path.join(settings["world_path"],
                                               target_name)
    else:
        if not os.path.isdir(settings["target_path"]):
            raise ValueError("The target directory '{}' does not exist.")
        ignore_paths.append(settings["target_path"].lower())
    print("Using settings: {}".format(settings))
    print("* found '{}' (using world "
          "'{}')...".format(good_flag, settings["world_path"]))
    # if settings.get("target_path") is None:
    #     settings["target_path"] = os.path.join(dest_path, target_name)
    if settings["world_path"] == settings["target_path"]:
        raise RuntimeError("The target path is same as the source path.")
    if os.path.isdir(settings["target_path"]):
        if settings.get("force") is True:
            shutil.rmtree(settings["target_path"])
            if os.path.isdir(settings["target_path"]):
                raise RuntimeError("Removing '{}' (with --force) failed"
                                   ".".format(settings["target_path"]))
            else:
                print("* removed '{}' (due to using --force option)"
                      ".".format(settings["target_path"]))
            os.mkdir(settings["target_path"])
        else:
            if not is_empty(settings["target_path"]):
                raise RuntimeWarning("'{}' contains files. You should"
                                     " delete it before running this"
                                     " script or use --force"
                                     ".".format(settings["target_path"]))
    else:
        # Code further up checks if should exist and stops if in that
        # case, so creating it now is OK.
        os.mkdir(settings["target_path"])
    extract(settings["world_path"], settings["target_path"])
    sys.stderr.write("Extracted {} file(s).\n".format(total))
    sys.stderr.write("New names are same as compressed names,"
                     " but are in {}.".format(settings["target_path"]))

if __name__ == "__main__":
    main()
