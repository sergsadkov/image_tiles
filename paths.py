# Auxillary functions for working with file paths

# Based on the original code by Sergei Sadkov from
# https://github.com/sergsadkov/gdal_format

import os
import shutil
import re
import time


def SplitPath(path):
    if os.path.isdir(path):
        return path, '', ''
    folder, file = os.path.split(path)
    name, ext = os.path.splitext(file)
    return folder, name, ext[1:]


def FullPath(folder, file, ext = ''):
    return f'{folder}\\{file}{("",".")[bool(ext)]}{ext.lstrip(".")}'


def SureDir(*folders):
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)


def CopyFile(path_in, path_out, overwrite = False):
    if (not os.path.exists(path_out)) or overwrite:
        if os.path.exists(path_in):
            try:
                shutil.copyfile(path_in, path_out)
            except Exception as e:
                pass


def DeleteFile(file):
    if os.path.exists(file):
        try:
            os.remove(file)
        except Exception as e:
            pass


def CopySHP(file_in, file_out, overwrite = False, ext_list = ['shp', 'dbf', 'shx', 'prj', 'sbn', 'sbx', 'cpg']):
    folder_in, name_in, ext_in = SplitPath(file_in)
    folder_out, name_out, ext_out = SplitPath(file_out)
    for ext in ext_list:
        CopyFile(FullPath(folder_in, name_in, ext), FullPath(folder_out, name_out, ext), overwrite = overwrite)


def DeleteSHP(file, ext_list = ['shp', 'dbf', 'shx', 'prj', 'sbn', 'sbx', 'cpg']):
    folder, name, ext = SplitPath(file)
    for ext in ext_list:
        DeleteFile(FullPath(folder, name, ext))


def Files(folder, extensions = None, target_path = None, miss_path = None):
    files = []
    if extensions is not None:
        if isinstance(extensions, (tuple, list)):
            extensions = list(extensions)
        else:
            extensions = [extensions]
        exts = ['.' + str(ext).lower().lstrip('.') for ext in extensions]
    for corner, _folders, _files in os.walk(folder):
        if miss_path:
            if re.search(miss_path, corner):
                continue
        for file in _files:
            if miss_path:
                if re.search(miss_path, file):
                    continue
            if extensions is not None:
                if all(not file.lower().endswith(ext) for ext in exts):
                    continue
            if target_path:
                if not re.search(target_path, file):
                    continue
            files.append(corner + '\\' + file)
    return files


def CheckPathValidity(path, forbid_none, must_exist, must_not_exist, must_folder_exist):
    if path is None:
        if forbid_none:
            return 'Path not set'
    elif os.path.exists(path):
        if must_not_exist:
            return f'File exists: {path}'
    else:
        if must_exist:
            return f'File not found: {path}'
        elif must_folder_exist and not os.path.exists(os.path.split(path)[0]):
            return f'Folder does not exist: {os.path.split(path)[0]}'


# Temp files functions

TEMP_DIR = os.path.join(os.environ['TMP'], 'image_processor')

def TempFolder():
    i = 0
    temp_folder = f'{TEMP_DIR}\\{i}'
    while os.path.exists(temp_folder):
        i += 1
        temp_folder = f'{TEMP_DIR}\\{i}'
    os.makedirs(temp_folder)
    return temp_folder


def TempName(name = 'tmp', ext = ''):
    temp_folder = TempFolder()
    return FullPath(temp_folder, name, ext)


class TempFiles:

    def __init__(self):
        self.delete = []
        self.delshp = []
        self.copy = {}
        self.copyshp = {}

    def CheckArg(self, arg):
        if isinstance(arg, str):
            if re.search(r'^\\+172\.', arg):
                name = os.path.split(arg)[1]
                if name:
                    new_arg = TempName(name)
                    if os.path.exists(arg):
                        if name.lower().endswith('.shp'):
                            CopySHP(arg, new_arg)
                            self.delshp.append(new_arg)
                        else:
                            CopyFile(arg, new_arg)
                            self.delete.append(new_arg)
                    elif name.lower().endswith('.shp'):
                        self.copyshp[new_arg] = arg
                    else:
                        self.copy[new_arg] = arg
                    return new_arg
        elif isinstance(arg, (tuple, list)):
            to_list = isinstance(arg, list)
            args, kwargs = self.CheckArgsKwargs(*tuple(arg), **{})
            if to_list:
                args = list(args)
            return args
        return arg

    def CheckArgsKwargs(self, *args, **kwargs):
        args_list = list(args)
        kwargs_dict = dict(kwargs)
        for i, arg in enumerate(args_list):
            args_list[i] = self.CheckArg(arg)
        for key in kwargs_dict:
            arg = kwargs_dict[key]
            kwargs_dict[key] = self.CheckArg(arg)
        return tuple(args_list), dict(kwargs_dict)

    def __del__(self):
        for new_arg in self.copy:
            CopyFile(new_arg, self.copy[new_arg])
            DeleteFile(new_arg)
        for new_arg in self.copyshp:
            CopySHP(new_arg, self.copyshp[new_arg])
            DeleteSHP(new_arg)
        for new_arg in self.delete:
            DeleteFile(new_arg)
        for new_arg in self.delshp:
            DeleteSHP(new_arg)


def StopFromStorage(func):
    def wrapped(*args, **kwargs):
        temp_files = TempFiles()
        args, kwargs = temp_files.CheckArgsKwargs(*args, **kwargs)
        res = func(*args, **kwargs)
        del temp_files
        return res
    return wrapped


# Create tempdir
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Delete all files with last change over 1 day ago from TEMP_DIR
for corner, folders, names in os.walk(TEMP_DIR):
    for name in names:
        file = FullPath(corner, name)
        if ((time.time()-os.path.getmtime(file))/86400 > 1):
            DeleteFile(file)
    if len(os.listdir(corner))==0:
        if corner != TEMP_DIR:
            os.rmdir(corner)
