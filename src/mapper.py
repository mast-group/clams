import os
import re

from lxml import etree

namespaces = {'src': 'http://www.srcML.org/srcML/src'}


def get_callers_info(callers_file, callers_package, callers):
    """
    Tries to create a map between the top callers and its associated file, using a best effort approach, by parsing the
    package declaration, in case this is need. If a file matches to a caller in the dataset, it retrieves any required
    information for the caller, and stores it to a dictionary. This includes the package,class,method and file names.

    :type callers_file: list
    :param callers_file: filename of the callers
    :type callers_package: list
    :param callers_package: package name of the callers
    :type callers: list
    :param callers: a list containing the top callers of each cluster
    :return a dictionary which is the map between top callers and their associated files, containing any required
    information
    """
    callers_info = {}
    for caller_id in range(len(callers)):
        caller = callers[int(caller_id)]
        package_class, method = caller.rsplit('.', 1)
        if callers_package[caller_id] != '':
            classname = package_class.rsplit(callers_package[caller_id] + '.', 1)[1]
        else:
            classname = package_class
        caller_info = {'id': caller_id, 'package': callers_package[caller_id], 'classname': classname, 'method': method,
                       'filename': callers_file[caller_id]}

        callers_info[caller] = caller_info
    return callers_info


def get_caller_info(caller_info, xml_dir):
    """
    Tries to match a given caller to its associated file.

    :type caller_info: dictionary
    :param caller_info: contains information for the client code (e.g. package name, classname, etc.)
    :type xml_dir: string
    :param xml_dir: the directory that contains the extracted xml files, associated with the client files
    """
    # if no package found, try to find the file using only the caller's info
    if not caller_info['package']:
        caller_info['filename'] = caller_info['classname']
        return

    files = [f[:-4] for f in os.listdir(xml_dir) if re.match(caller_info['classname'] + '(_\d+)?' + '.xml', f)]
    found = False
    while caller_info['package'] > 0 and found == False:
        # found files with this classname
        # check if this is the file we are looking for, using its package declaration statement
        if len(files) > 0:
            for f in files:
                filepath = os.path.join(xml_dir, f + '.xml')
                if find_target_client(filepath, caller_info['package']):
                    caller_info['filename'] = f
                    found = True
                    break
            # this will execute in case of normal execution of the loop (no break)
            # this happens in the rare case of a file with the same name (bad luck!)
            else:
                if len(caller_info['package'].rsplit('.', 1)) > 1:
                    files = split_and_search(caller_info, xml_dir)
                    continue
                else:
                    break
            break
        # no files with this classname
        # probably in case of a nested class -> split package name again
        else:
            files = split_and_search(caller_info, xml_dir)
            for f in files:
                filepath = os.path.join(xml_dir, f + '.xml')
                if find_target_client(filepath, caller_info['package']):
                    caller_info['filename'] = f
                    found = True
                    break
            else:
                continue
            break


def split_and_search(caller_info, xml_dir):
    """
    Tries to match the caller to its associated client file, by splitting the fully qualified name of the class.

    :type caller_info: dictionary
    :param caller_info: contains information for the client code (e.g. package name, classname, etc.)
    :type xml_dir: string
    :param xml_dir: the directory that contains the extracted xml files, associated with the client files
    :return files: a list of files with the target filename
    """
    caller_info['package'], classname = caller_info['package'].rsplit('.', 1)
    caller_info['classname'] = classname + '.' + caller_info['classname']
    # list all java files with the target file name (or even a similar one)
    # e.g. Main.java, Main_1
    files = [os.path.splitext(f)[0] for f in os.listdir(xml_dir) if
             re.match(caller_info['classname'].split('.')[0] + '(_\d+)?' + '.xml', f)]
    return files


def find_target_client(filepath, package):
    """
    Parses the package declaration (if available) of a java file, and checks whether it matches to the
    given package name.

    :type filepath: str
    :param filepath: the path of the file to be parsed
    :type package: str
    :param package: the package to be matched
    :return True if the package in the file matches the given one, False otherwise
    """
    root = etree.parse(filepath).getroot()
    package_query = './/src:package/src:name'
    package_el = root.xpath(package_query, namespaces=namespaces)
    if package_el:
        # retrieve the full package name, by traversing the appropriate xml element iteratively
        package_found = ''.join(itertext(package_el[0]))
        if package_found == package:
            return True
    return False


def itertext(self):
    """
    Traverses an xml element iteratively.
    """
    tag = self.tag
    if not isinstance(tag, str) and tag is not None:
        return
    if self.text:
        yield self.text
    for e in self:
        for s in e.itertext():
            yield s
        if e.tail:
            yield e.tail
