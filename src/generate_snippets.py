import os
from lxml import etree

from src.helper import filefunctions
from summarise import Summariser


class SnippetGenerator:

    def __init__(self, res_dir, top_files, callers_info, callers, calls, class_vars):
        """
        :type res_dir: str
        :param res_dir: the directory where the results of the current session are stored
        :type top_files: a dictionary of lists
        :param top_files: a dictionary of sorted lists that contain top callers for each cluster
        :type callers: list
        :param callers: a list of caller methods
        :type calls: list of lists
        :param calls: a list of method call sequences
        :type class_vars: dictionary
        :param class_vars: contains the declared variables (e.g. class variables) for each file
        """
        self.res_dir = res_dir
        self.top_files = top_files
        self.callers_info = callers_info
        self.callers = callers
        self.calls = calls
        self.class_vars = class_vars
        self.namespaces = {'src': 'http://www.srcML.org/srcML/src'}


    def perform_snippet_generation(self, params):
        """
        Extracts a candidate pattern for each of the top files.

        :type params: dictionary
        :param params: {'summarise','resolve_types','remove_non_api'}
        """
        xml_dir = os.path.join(self.res_dir, 'methodFiles')
        minimiser = Summariser(self.namespaces)
        self.patterns_name_id_map = {}
        for key, value in self.top_files.iteritems():
            cluster_map = {}
            for top_file in value:
                caller = top_file['caller']
                xml_path = os.path.join(xml_dir, self.callers_info[caller]['filename'] + '_' +
                                        self.callers_info[caller]['method'] + '.xml')
                # check if this file exists/has been parsed successfully
                if not os.path.isfile(xml_path):
                    continue
                filename = self.callers_info[caller]['filename'] + '_' + self.callers_info[caller]['method'] + '.xml'
                cluster_map[filename] = self.calls[self.callers_info[caller]['id']]
                root = etree.parse(xml_path).getroot()
                vars_decl = self.class_vars[str(self.callers_info[caller]['filename'] + '_' +
                                                self.callers_info[caller]['method'])]
                self.get_params(root, vars_decl)
                block_el = self.find_block(root)
                if block_el is None: continue
                if params['summarise']:
                    params_sum = {'resolve_types': params['resolve_types'], 'remove_non_api': params['remove_non_api']}
                    element = minimiser.summarise(block_el, self.calls[self.callers_info[caller]['id']],
                                                  vars_decl, params=params_sum)
                    element = self.fix_parentheses(element)
                else:
                    element = self.fix_parentheses(block_el)
                element.tail = None
                filefunctions.write_pattern_xml(self.res_dir, str(key), self.callers_info[caller]['filename'],
                                                self.callers_info[caller]['method'], etree.tostring(element))
            self.patterns_name_id_map[str(key)] = cluster_map


    def get_params(self, root, vars_decl):
        """
        Finds the declared parameters of the client method, if any, and adds them to the appropriate dictionary.
        This information will be used from the summariser, in order to resolve variables type.

        :type root: Element
        :param root: the root of the xml document
        :type vars_decl: dictionary
        :param vars_decl: the cvariables that have been declared at a previous point
        """
        param_query = './src:parameter_list/src:parameter/src:decl[src:type and src:name]'
        for param in root.xpath(param_query, namespaces=self.namespaces):
            type = param.xpath('./src:type', namespaces=self.namespaces)[0]
            name = param.xpath('./src:name', namespaces=self.namespaces)[0].text
            if type is not None and name is not None:
                vars_decl[name] = {'type': type}


    def fix_parentheses(self, root):
        """
        Inserts missing parentheses in Block statements.

        :type root: Element
        :param root: the root of the subtree
        :return root: the update root
        """
        xpath_query = "//src:block/*[last()]"
        for elem in root.xpath(xpath_query, namespaces=self.namespaces):
            if elem.tail is None:
                elem.tail = '}'
            elif elem.tail.strip() != '}':
                elem.tail = '}'

        xpath_query = "//src:block[@type='pseudo']"
        for elem in root.xpath(xpath_query, namespaces=self.namespaces):
            elem.attrib.pop('type')
            elem.text = '{'
        return root


    def find_calls_xpath(self, caller):
        """
        Forms an XPath query for a top caller. This query looks for API method calls inside a given client code.

        :type caller: str
        :param caller: a caller of the dataset (fully qualified method name)
        :return xpath_query: an XPath query
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
        return xpath_query


    def find_block(self, root):
        """
        Retrieves the block xml Element of a given root.

        :type root: Element
        :param root: the root of the xml document
        :return block_el: the Element associated with the block. None if not found.
        """
        block_el = root.xpath('./src:block', namespaces=self.namespaces)[0]
        return block_el


    def find_lca(self, root, xpath_query):
        """
        Finds the Lowest Common Ancestor (xml element) of a list of xml elements. The xml elements are extracted based
        on a given XPath expression. THe Longest Common Ancestor of the is found using the following concept:
            - The LCA's depth is <= min of all elements' depths. As a result, for each element whose depth is > min,
              visit its parent, until the requested depth has been achieved
            - Having elements of the same depth, visit their parents until a common parent has been identified. The
              worst case scenario retrieves the root of the xml file.
        Note: not used in the actual implementation as a summarisation algorithm has been implemented for this purpose.

        :type root: Element
        :param root: the root of the xml document
        :type xpath_query: str
        :param xpath_query: an Xpath query
        :return element: the lowest common ancestor found (type Element), None if the XPATH query did not return any
        Elements
        """
        depths = []
        elems = []
        for seq in root.xpath(xpath_query, namespaces=self.namespaces):
            depths.append(int(seq.xpath('count(ancestor::*)')))
            elems.append(seq)
        if len(elems) == 0:
            return None
        min_depth = min(depths)
        for e in range(len(elems)):
            for _ in range(depths[e] - min_depth):
                elems[e] = elems[e].getparent()
        while not all(etree.tostring(x) == etree.tostring(elems[0]) for x in elems):
            for e in range(len(elems)):
                elems[e] = elems[e].getparent()
        element = elems[0]
        # suppress any trailing text
        element.tail = None
        return element
