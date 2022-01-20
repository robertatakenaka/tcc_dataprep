
import os
import csv
# import numpy as np


def create_folder(*args):
    path = os.path.join(*args)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def write_file(file_path, content, mode="w"):
    with open(file_path, mode) as fp:
        fp.write(content)


def read_file(file_path):
    with open(file_path, "r") as fp:
        return fp.read()


def read_csv_file(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row


# def write_array(file_path, arr):
#     np.save(file_path, arr, allow_pickle=True, fix_imports=True)


def read_array(file_path):
    return np.load(file_path, mmap_mode="r")


def split_file_in_n_files(file_path, folder_path, n, prefix=None):
    if not prefix:
        prefix = os.path.basename(file_path)
    name, ext = os.path.splitext(file_path)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    files = [
        os.path.join(folder_path, f"{prefix}_{i}{ext}")
        for i in range(1, n+1)
    ]
    for _file_path in files:
        write_file(_file_path, "")

    with open(file_path) as fp:
        i = 0
        for row in fp.readlines():
            write_file(files[i], row, "a")
            i += 1
            if i == n:
                i = 0
