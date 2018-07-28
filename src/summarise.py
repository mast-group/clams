from lxml import etree
import re


class Summariser:
    def __init__(self, namespaces):
        """
        :type namespaces: dictionary
        :param namespaces: the namespace used by the srcml tool
        """
        self.namespaces = namespaces

        self.statements = ['return', 'assert', 'throw', 'empty_stmt', 'decl_stmt', 'expr_stmt']
        self.controls = ['condition', 'control', 'case', 'default']
        self.blocks = ['if', 'while', 'for', 'do', 'while', 'switch', 'try', 'function', 'class', 'enum']

    def summarise(self, root, calls, vars_decl, params):
        """
        Summarises a given tree, using a novel summarisation algorithm that has been implemented. The main features of
        the algorithm may be summarised to the points below:
            - Removes comments
            - Replaces literals with their srcML type
            - Resolves variables type
            - Adds descriptive comments in empty blocks
            - Removes non-API statements
            - Adds descriptive comments for variables declared in API statements, that are only used in non-API
            statements (which are removed from the tree).

        :type root: Element
        :param root: the root of the tree to be summarised
        :type calls: list of lists
        :param calls: a list of method call sequences
        :type vars_decl: dictionary
        :param vars_decl: the already declared variables
        :type params; dictionary
        :param params: {'remove_non_api', 'resolve_types'}
        :return block_root: the root of the summarised tree
        """
        # remove comments
        self.remove_comments(root)
        # replace literals with their type
        self.replace_literals(root)

        # retrieve all declared variables
        self.get_vars(root, vars_decl)

        # classify statements into API and non-API ones
        methods = self.form_calls(calls)
        all_non_api, api_stats = self.get_statements(root, methods)

        # remove non-API statements
        if params['remove_non_api']:
            self.remove_stats(all_non_api)

        # check which of the retrieved variables should be declared to the summarised snippet
        self.check_vars(root, vars_decl)

        # get variables declared in API statements that are only used in non-API statements
        vars_wrt = self.get_api_writes(api_stats)
        self.get_api_reads(vars_wrt, api_stats)

        # fix parenthesis issue
        block_root = root
        if root.tag.split('}', 1)[1] != 'block':
            block_root = etree.Element("{http://www.srcML.org/srcML/src}block", nsmap=self.namespaces)
            block_root.text = '{\n'
            block_root.append(root)

        # resolve variables type and add descriptive comments for the appropriate variables
        if params['resolve_types']:
            self.add_decl(block_root, vars_decl)
        if params['remove_non_api']:
            self.add_forward_comments(vars_wrt)

        # find empty blocks and add descriptive comments
        block_stmt = self.find_empty_block()
        for elem in root.xpath(block_stmt, namespaces=self.namespaces):
            comment_depth = int(elem.xpath('count(ancestor::*)'))
            comment = etree.Element("comment", type="line")
            comment.text = str(4 * comment_depth * ' ') + '// Do something \n'
            elem.text = '{\n'
            # elem.text = elem.text.replace('}', '')
            elem.append(comment)

        # take care of switch-case statements when adding descriptive comments!
        case_stmt = self.find_empty_case()
        for elem in root.xpath(case_stmt, namespaces=self.namespaces):
            if elem.getnext().tag.split('}', 1)[1] == 'break':
                comment_depth = int(elem.xpath('count(ancestor::*)')) + 1
                comment = etree.Element("comment", type="line")
                comment.text = str(4 * comment_depth * ' ') + '// Do something \n'
                elem.tail = '\n'
                par = elem.getparent()
                pos = par.index(elem)
                par.insert(pos + 1, comment)

        # block_root = self.remove_empty_lines(block_root)

        return block_root

    @staticmethod
    def form_calls(calls):
        """
        Retrieves the API method names from their fully qualified names.

        :type calls: list
        :param calls: the API methods invoked in the client method
        :return methods: the API method names
        """
        methods = []
        for call in calls:
            new_call = call.rsplit('.', 1)[1]
            if new_call == '<init>':
                new_call = call.rsplit('.', 2)[1]
            methods.append(new_call)
        return methods

    def remove_comments(self, root):
        """
        Removes comments.

        :type root: Element
        :param root: the root of the tree
        """
        comment_stmt = self.find_comment()
        for elem in root.xpath(comment_stmt, namespaces=self.namespaces):
            elem.getparent().remove(elem)

    def replace_literals(self, root):
        """
        Replaces literals with their srcML type.

        :type root: Element
        :param root: the root of the tree
        """
        literals = self.find_literals()
        for elem in root.xpath(literals, namespaces=self.namespaces):
            elem.text = elem.get('type')

    def get_statements(self, root, methods):
        """
        Classifies statements into API and non-API ones.

        :type root: Element
        :param root: the root of the tree
        :type methods: list
        :param methods: the API methods invoked in the lcient method
        :return all_non_api: the non-API statements
        :return all_api: the API statements
        """
        all_non_api = []
        api_stats = []
        calls_query = self.form_calls_xpath(methods)
        for node in root.getiterator():
            if node.tag.split('}', 1)[1] in self.statements:
                if node.xpath(calls_query, namespaces=self.namespaces):
                    api_stats.append(node)
                else:
                    all_non_api.append(node)
            elif node.tag.split('}', 1)[1] in self.controls:
                if node.getparent().xpath(calls_query, namespaces=self.namespaces):
                    api_stats.append(node)
            elif node.tag.split('}', 1)[1] in self.blocks:
                if not node.xpath(calls_query, namespaces=self.namespaces):
                    par = node.getparent()
                    if par.tag.split('}', 1)[1] != 'expr':
                        all_non_api.append(node)

        return all_non_api, api_stats

    @staticmethod
    def form_calls_xpath(methods):
        """
        Forms an XPath expression that looks for the API methods invoked in the client method.

        :type methods: list
        :param methods: the API methods invoked in the client method
        :return xpath_query: an XPath expression
        """
        join_calls = "' or .//src:name='".join(methods)
        xpath_query = ".//src:call[.//src:name='" + join_calls + "']"
        return xpath_query

    def get_vars(self, root, vars_decl):
        """
        Finds any variables declared in the client method and adds them the appropriate dictionary. This information is
        then used in order to resolve variables type.

        :type root: Element
        :param root: the root of the tree
        :type vars_decl: dictionary
        :param vars_decl: the variables declared at a previous point
        """
        for node in root.getiterator():
            if node.tag.split('}', 1)[1] == 'decl':
                type_l = node.xpath('./src:type', namespaces=self.namespaces)
                name_l = node.xpath('./src:name', namespaces=self.namespaces)
                if type_l and name_l:
                    type = type_l[0]
                    name = name_l[0].text
                    if type is not None and name is not None:
                        vars_decl[name] = {'type': type}

    def check_vars(self, root, vars_decl):
        """
        Checks which of the variables declared in the client code are used in the summarised code.

        :type root: Element
        :param root: the root of the tree
        :type vars_decl: dictionary
        :param vars_decl: the variables declared at a previous point
        """
        # check if variable is used at any point in the summarised snippet
        for name in vars_decl.keys():
            query = ".//src:name[.='" + name + "']"
            read_name = root.xpath(query, namespaces=self.namespaces)
            if not read_name:
                del vars_decl[name]

        # check if a used variable has already been defined in the summarised snippet
        for node in root.getiterator():
            if node.tag.split('}', 1)[1] == 'decl':
                name_l = node.xpath('./src:name', namespaces=self.namespaces)
                if name_l:
                    name = name_l[0].text
                    if name is not None:
                        if name in vars_decl:
                            del vars_decl[name]

    def get_api_writes(self, api_stats):
        """
        Finds the variables declared in API statements and stores them to a dictionary.

        :type api_stats: list
        :param api_stats: contains the elements associated with the API statements of the tree
        :return vars_wrt: the variables declared in API statements
        """
        vars_wrt = []
        for i in range(len(api_stats)):
            if api_stats[i].tag.split('}', 1)[1] == 'decl_stmt':
                name = api_stats[i].xpath('.//src:decl/src:name', namespaces=self.namespaces)[0].text
                if name:
                    d = {'name': name, 'forward': False, 'pos': i, 'write-el': api_stats[i]}
                    vars_wrt.append(d)

            # this is in case a variable has been declared at a previous point and is now redefined in an API
            # statement
            if api_stats[i].tag.split('}', 1)[1] == 'expr_stmt':
                decl_expr = api_stats[i].xpath("./src:expr[src:name and src:operator[.='=']]",
                                               namespaces=self.namespaces)
                if decl_expr:
                    name_l = decl_expr[0].xpath('./src:name', namespaces=self.namespaces)
                    if name_l:
                        name = name_l[0].text
                        if name:
                            d = {'name': name, 'forward': False, 'pos': i, 'write-el': api_stats[i]}
                            vars_wrt.append(d)

        return vars_wrt

    def get_api_reads(self, vars_wrt, api_stats):
        """
        Checks whether the variables declared in API statements are used in other API statements after that point.

        :type vars_wrt: dictionary
        :param vars_wrt: the variables declared in API statements
        :type api_stats: list
        :param api_stats: contains the elements associated with the API statements of the tree
        :return vars_wrt: an updated dictionary which contains information about the use of API variables in other API
        statements
        """
        for var in vars_wrt:
            for i in range(var['pos'] + 1, len(api_stats)):
                query = ".//src:name[.='" + var['name'] + "']"
                name = api_stats[i].xpath(query, namespaces=self.namespaces)
                if name:
                    var['forward'] = True
                    break
        return vars_wrt

    def add_decl(self, root, vars_decl):
        """
        Adds a declarement statement for each of the variables used in the summarised snippet, for which there exists
        no such statement. It basiccaly resolves variables type.

        :type root: Element
        :param root: the root of the tree
        :type vars_decl: dictionary
        :param vars_decl: the variables declared at a previous point
        """
        for name, attrs in vars_decl.items():
            decl_stmt = etree.Element("{http://www.srcML.org/srcML/src}decl_stmt", nsmap=self.namespaces)
            decl_stmt.tail = '\n' + 8 * ' '
            declaration = etree.Element("{http://www.srcML.org/srcML/src}decl", nsmap=self.namespaces)
            declaration.tail = ';'

            decl_name = etree.Element("{http://www.srcML.org/srcML/src}name", nsmap=self.namespaces)
            decl_name.text = name

            declaration.append(attrs['type'])
            declaration.append(decl_name)

            decl_stmt.append(declaration)
            root.insert(0, decl_stmt)

    def add_forward_comments(self, vars_wrt):
        """
        Adds descriptive comments for the variables that are declared in API statements and used in non-APi statements.

        :type vars_wrt: dictionary
        :param vars_wrt: the variables declared in API statements
        """
        for var in vars_wrt:
            if var['forward'] == False:
                comment = etree.Element("{http://www.srcML.org/srcML/src}comment", type="line", nsmap=self.namespaces)
                comment_depth = int(var['write-el'].xpath('count(ancestor::*)'))
                comment.text = str(4 * comment_depth * ' ') + '// Do something with ' + var['name'] + '\n'
                api_wrt_parent = var['write-el'].getparent()
                comment.tail = api_wrt_parent[-1].tail
                api_wrt_parent[-1].tail = '\n'
                api_wrt_parent.append(comment)

    @staticmethod
    def remove_stats(all_non_api):
        """
        Removes non-API statements by iterating the tree in reverse order (reverse bottom-up pre-order traversal).

        :type all_non_api: list
        :param all_non_api: the non-API statements
        """
        for i in range(len(all_non_api) - 1, -1, -1):
            all_non_api[i].getparent().remove(all_non_api[i])

    @staticmethod
    def remove_empty_lines(block_root):
        """
        Removes empty lines in the summarised snippet.
        Note: not used in the actual implementation.

        :type block_root: Element
        :param block_root: the root of the block of the client method
        :return block_root: the root of the updated tree
        """
        text = etree.tostring(block_root)
        text = re.sub("(?m)^[ \t]*\r?\n", "", text)
        block_root = etree.fromstring(text).getroot()
        return block_root

    @staticmethod
    def find_comment():
        """
        XPath expression to find comments.

        :return xpath_query: XPath expression
        """
        xpath_query = ".//src:comment"
        return xpath_query

    @staticmethod
    def find_empty_block():
        """
        XPath expression to find empty blocks.

        :return xpath_query: XPath expression
        """
        xpath_query = ".//src:block[not (*)]"
        return xpath_query

    @staticmethod
    def find_empty_case():
        """
        XPath expression to find empty blocks in 'case' statements.

        :return xpath_query: XPath expression
        """
        xpath_query = ".//src:case"
        return xpath_query

    @staticmethod
    def find_literals():
        """
        XPath expression to find literals.

        :return xpath_query: XPath expression
        """
        xpath_query = ".//src:literal"
        return xpath_query
