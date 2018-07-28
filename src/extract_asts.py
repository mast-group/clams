import os
import subprocess
from lxml import etree

from src.helper import filefunctions


class ASTExtractor:
    def __init__(self, res_dir, callers, calls, parser_path):
        """
        :type res_dir: str
        :param res_dir: the directory where the results of the current session are stored
        :type callers: list
        :param callers: a list of caller methods
        :type calls: list of lists
        :param calls: a list of method call sequences
        :type parser_path: str
        :param parser_path: the path of the srcml executable
        """
        self.res_dir = res_dir
        self.callers = callers
        self.calls = calls
        self.parser_path = parser_path
        self.xml_path = ''
        self.class_vars = {}
        self.namespaces = {'src': 'http://www.srcML.org/srcML/src'}

    def extract_asts(self):
        """
        Calls the appropriate functions to extract the ASTs.
        """
        self.parse_files()
        self.split_xml()

    def parse_files(self):
        """
        Parses the files using the srcml tool, and extracts their AST representation, in the srcML format. The results
        are then stored in a merged xml file.
        """
        src_directory = os.path.join(self.res_dir, 'srcFiles')
        self.xml_path = os.path.join(self.res_dir, 'asts.xml')
        p = subprocess.Popen([self.parser_path, src_directory, '-o', self.xml_path],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.communicate()[0]
        assert os.path.isfile(self.xml_path)

    def split_xml(self):
        """
        Generates single xml files from the merged xml file.
        """
        root = etree.parse(self.xml_path).getroot()
        namespaces = {'src': 'http://www.srcML.org/srcML/src'}
        xpath_query = ".//src:unit[@filename]"
        for unit in root.findall(xpath_query, namespaces):
            content = etree.tostring(unit)
            src_filepath = unit.get('filename')
            filefunctions.write_file_srcml(src_filepath, self.res_dir, content)

    def create_methods_xml(self, callers_info):
        """
        Extracts the appropriate client methods from the xml files, and writes them to new xml files.

        :type callers_info: dictionary
        :param callers_info: stores the information extracted by the mapping between the .arff file and the client code
        (filenames, client method names, etc.)
        """
        xml_dir = os.path.join(self.res_dir, 'xmlFiles')
        for key, value in callers_info.iteritems():
            xml_path = os.path.join(xml_dir, value['filename'] + '.xml')
            root = etree.parse(xml_path).getroot()
            xpath_query = self.form_method_xpath(value['classname'], value['method'])
            # get method element
            method_element = self.find_method_element(root, xpath_query, key)
            if method_element is None: continue
            class_vars = self.get_class_vars(root, value['classname'])
            self.get_all_vars(root, method_element, class_vars)
            self.class_vars[value['filename'] + '_' + value['method']] = class_vars
            filefunctions.write_method_xml(self.res_dir, value['filename'], value['method'],
                                           etree.tostring(method_element))

    @staticmethod
    def form_method_xpath(classname, method):
        """
        Forms an XPath query for a top caller. This query looks for the requested client method inside a given client
         code.

        :type classname: str
        :param classname: the name of the class where the requested method is stored (fully qualified name, if method is
        inside a nested class)
        :type method: list
        :param method: the name of the method
        :return xpath_query: an XPath query
        """
        xpath_query = './/'
        for c in classname.split('.'):
            c_name = c
            xpath_query += "src:class[src:name='" + c + "']//"
        if method == c_name:
            xpath_query += "src:constructor[src:name='" + method + "']"
        else:
            xpath_query += "src:function[src:name='" + method + "']"
        return xpath_query

    def get_class_vars(self, root, classname):
        """
        Finds the class variables declared in the original xml file, and stores them to a dictionary. This information
        will be used from the summariser, in order to resolve variables type.

        :type root: Element
        :param root: the root of the xml document
        :type classname: string
        :param classname: the classname of the file
        :return class_vars_decl: a dictionary that stores the name and the type of any class variables
        """
        c_names = "' or src:name='".join(classname.split('.'))
        decl_xpath = "src:block/src:decl_stmt[src:decl[src:type and src:name]]"
        xpath_query = ".//src:class[src:name='" + c_names + "']/" + decl_xpath
        class_vars_decl = {}
        for decl in root.xpath(xpath_query, namespaces=self.namespaces):
            type_l = decl.xpath('.//src:decl/src:type', namespaces=self.namespaces)
            name_l = decl.xpath('.//src:decl/src:name', namespaces=self.namespaces)
            if type_l and name_l:
                type = type_l[0]
                name = name_l[0].text
                if type is not None and name is not None:
                    class_vars_decl[name] = {'type': type}
        return class_vars_decl

    def get_all_vars(self, root, method_element, class_vars):
        """
        Finds any variables declared at any level of the source code, before the target client method, and adds them
        to the dictionary that already contains the class variables. This includes variables declared for instance
        inside methods that probably contain the target client method. This information will be used from the
        summariser, in order to resolve variables type.

        :type root: Element
        :param root: the root of the xml document
        :type method_element: Element
        :param method_element: the xml Element of the target client method
        :type class_vars: dictionary
        :param class_vars: stores the class variables that have been found so far
        """
        for node in root.getiterator():
            if node == method_element:
                break

            if node.tag.split('}', 1)[1] == 'decl_stmt':
                type_l = node.xpath('.//src:decl/src:type', namespaces=self.namespaces)
                name_l = node.xpath('.//src:decl/src:name', namespaces=self.namespaces)
                if type_l and name_l:
                    type = type_l[0]
                    name = name_l[0].text
                    if type is not None and name is not None:
                        class_vars[name] = {'type': type}

    def find_method_element(self, root, xpath_query, caller):
        """
        Finds the requested client method inside a given client code, using an XPath expression.

        :type root: Element
        :param root: the root of the xml document
        :type xpath_query: str
        :param xpath_query: an XPath query
        :type caller: str
        :param caller: a caller of the dataset (fully qualified method name)
        :return method_element: the xml Element associated with the target client method, None if the XPath query did
        not return any Elements
        """
        namespaces = {'src': 'http://www.srcML.org/srcML/src'}
        method_elements = root.xpath(xpath_query, namespaces=namespaces)
        if not method_elements:
            return None
        # check for method overloading
        if len(method_elements) > 1:
            xpath_query, calls_l = self.find_calls_xpath(caller)
            for m in method_elements:
                seq = m.xpath(xpath_query, namespaces=namespaces)
                if len(seq) >= len(calls_l):
                    method_element = m
                    break
            else:
                method_element = method_elements[0]
        else:
            method_element = method_elements[0]

        # remove trailing text, if any! Usually this includes brackets which are stored in the tail. We remove them at
        # this point, and write them back before writing the final result to a file.
        # this ensures that the xml is well-formed
        method_element.tail = None
        return method_element

    def find_calls_xpath(self, caller):
        """
        Forms an XPath query for a top caller. This query looks for API method calls inside a given client code.

        :type caller: str
        :param caller: a caller of the dataset (fully qualified method name)
        :return xpath_query: an XPath query
        :return calls_l: a list of API calls in caller
        """
        caller_idx = self.callers.index(caller)
        calls_l = self.calls[caller_idx]
        call = calls_l[0].rsplit('.', 1)[1]
        # check for constructor
        if call == '<init>':
            call = calls_l[0].rsplit('.', 2)[1]

        xpath_query = ".//src:call[.//src:name='" + call + "'"
        for j in range(1, len(calls_l)):
            call = calls_l[j].rsplit('.', 1)[1]
            if call == '<init>':
                call = calls_l[j].rsplit('.', 2)[1]
            xpath_query += " or .//src:name='" + call + "'"
        xpath_query += "]"

        return xpath_query, calls_l
