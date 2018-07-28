import sys
reload(sys)
sys.setdefaultencoding("utf8")
import os
import errno
import re
import json
import numpy as np
import shutil
from distutils.dir_util import copy_tree


def load_arff(arff_file_path, omit=6):
    """
    Loads the dataset (.arff file) and stores callers and calls in lists.

    :type arff_file_path: str
    :param arff_file_path: path of arff file
    :type omit: int
    :param omit: number of lines to be omitted from the arff file
    :return callerFile: filename of the caller
    :return callerPackage: package name of the caller
    :return caller: a list of client methods (callers)
    :return calls: a list of API method called by the corresponding client method
    """
    callerFile = []
    callerPackage = []
    caller = []
    calls = []
    # this pattern handles the case where a ',' character exists in a sequence
    # which is not handled by the liac-arff library
    pattern = re.compile(r"""'(?P<callerFile>.*?)'  # callerFile
                             ,'(?P<callerPackage>.*?)'  # callerPackage
                             ,'(?P<caller>.*?)'  # caller
                             ,'(?P<calls>.*?)' # calls
                             """, re.VERBOSE)

    with open(arff_file_path, 'r') as f:
        for _ in xrange(omit):
            next(f)
        for line in f:
            match = pattern.match(line)
            callerFile.append(match.group("callerFile"))
            callerPackage.append(match.group("callerPackage"))
            caller.append(match.group("caller"))
            # remove class type, if it exists (take care of constructors!)
            calls_group = match.group("calls")
            calls_group = re.sub('<(?!init).+?>+', '', calls_group)
            calls.append(calls_group.split())
    return callerFile, callerPackage, caller, calls


def write_to_file(filepath, content):
    """
    Writes content to file.

    :type filepath: str
    :param filepath: the path of the file where the content will be written
    :type content: str
    :param content: the contnet of the file
    """
    with open(filepath, 'w') as f:
        f.write(content)


def write_transaction(res_dir, cluster_id, transaction):
    """
    Writes a db of transactions to a .in file.

    :type res_dir: str
    :param res_dir: the directory where the results of the current session are stored
    :type cluster_id: int
    :param cluster_id: the id of the cluster that is associated with the transactions
    :type transaction: str
    :param transaction: the transaction
    """
    filepath = os.path.join(res_dir, 'transactions', str(cluster_id) + '.in')
    make_sure_dir_exists(os.path.dirname(filepath))
    with open(filepath, 'w') as f:
        f.write(transaction)


def write_file_srcml(src_filepath, res_dir, content):
    """
    Writes a db of transactions to a .in file.

    :type src_filepath: str
    :param src_filepath: the filepath of the src
    :type res_dir: str
    :param res_dir: the directory where the results of the current session are stored
    :type content: str
    :param content: the content of the file
    """
    #suppress file extension
    src_filepath = os.path.splitext(src_filepath)[0]
    path_split = src_filepath.rsplit(os.sep, 3)
    dir_path = os.path.join(res_dir, 'xmlFiles')
    filepath = os.path.join(dir_path, path_split[3] + '.xml')
    make_sure_dir_exists(dir_path)
    with open(filepath, 'w') as f:
        f.write(content)


def write_method_xml(res_dir, filename, method, content):
    """
    Writes method's content to xml.

    :type res_dir: str
    :param res_dir: the directory where the results of the current session are stored
    :type cluster_id: int
    :param cluster_id: the id of the cluster that is associated with the content
    :type filename: str
    :param filename: the filename to be used
    :type method: str
    :param method: method's name
    :type content: str
    :param content: the content of the file
    """
    dir_path = os.path.join(res_dir, 'methodFiles')
    filepath = os.path.join(dir_path, filename + '_' + method + '.xml')
    make_sure_dir_exists(dir_path)
    with open(filepath, 'w') as f:
        f.write(content)


def write_pattern_xml(res_dir, cluster_id, filename, method, content):
    """
    Writes method's content to xml.

    :type res_dir: str
    :param res_dir: the directory where the results of the current session are stored
    :type cluster_id: int
    :param cluster_id: the id of the cluster that is associated with the content
    :type filename: str
    :param filename: the filename to be used
    :type method: str
    :param method: method's name
    :type content: str
    :param content: the content of the file
    """
    dir_path = os.path.join(res_dir, 'patternFiles', cluster_id)
    filepath = os.path.join(dir_path, filename + '_' + method + '.xml')
    make_sure_dir_exists(dir_path)
    with open(filepath, 'w') as f:
        f.write(content)


def write_medoid_src(res_dir, cluster_id, content):
    """
    Writes method's content to xml.

    :type res_dir: str
    :param res_dir: the directory where the results of the current session are stored
    :type cluster_id: int
    :param cluster_id: the id of the cluster that is associated with the content
    :type filename: str
    :param filename: the filename to be used
    :type method: str
    :param method: method's name
    :type content: str
    :param content: the content of the file
    """
    medoids_dir = os.path.join(res_dir, 'pattern_medoids')
    make_sure_dir_exists(medoids_dir)
    filepath = os.path.join(medoids_dir, cluster_id + '.java')
    with open(filepath, 'w') as f:
        f.write(content)


def write_json(res_dir, filename, data):
    """
    Writes data to json file.

    :type filename: str
    :param filename: the name of the file that will store the data
    :type data: dict like
    :param data: the data to be written to file
    """
    filepath = os.path.join(res_dir, filename + '.json')
    make_sure_dir_exists(os.path.dirname(filepath))
    with open(filepath, 'w') as fp:
        json.dump(data, fp, indent=4)


def write_array(res_dir, filename, data):
    """
    Writes numpy array to file.

    :type filename: str
    :param filename: the name of the file that will store the data
    :type data: array like
    :param data: the data to be written to file
    """
    filepath = os.path.join(res_dir, filename + '.txt')
    make_sure_dir_exists(os.path.dirname(filepath))
    np.savetxt(filepath, data, fmt='%-7.2f')


def make_sure_dir_exists(directory):
    """
    Checks whether a directory exists and creates it in case it is missing.

    :type filename: str
    :param filename: the name of the file that will store the data
    :type directory: str
    :param directory: the directory to be created (if it does not exist)
    """
    try:
        os.makedirs(directory)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def delete_dir(directory):
    """
    Deletes a directory if it exists.

    :type directory: str
    :param directory: the directory to be deleted (if it exists)
    """
    if os.path.exists(directory):
        shutil.rmtree(directory)


def delete_files(directory, extension):
    filelist = [f for f in os.listdir(directory) if f.endswith(extension)]
    for f in filelist:
        filepath = os.path.join(directory, f)
        os.remove(filepath)

def delete_files_recurs(directory, extension):
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in [f for f in filenames if f.endswith(extension)]:
            filepath = os.path.join(directory, dirpath, filename)
            os.remove(filepath)


def count_dir_files(directory, extension):
    cnt = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for _ in [f for f in filenames if f.endswith(extension)]:
            cnt += 1
    return cnt


def copy_dir_files(src, dst):
    try:
        copy_tree(src, dst)
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise


def create_calls_files_map(directory, ranked_files_json, calls_files_json):
    ranked_files_path = os.path.join(directory, ranked_files_json)
    calls_files_map_path = os.path.join(directory, calls_files_json)
    with open(ranked_files_path) as infile:
        data = json.load(infile)

    calls = {}
    for i, d in enumerate(data):
        for call in d['calls']:
            calls.setdefault(call, []).append((i, d['name']))

    with open(calls_files_map_path, 'w') as outfile:
        json.dump(calls, outfile)
