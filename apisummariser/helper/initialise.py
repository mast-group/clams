import os

import filefunctions


def set_up(dataset):
    paths = Paths()
    # remove previous results
    paths.directory = os.path.join(os.getcwd(), 'results', dataset)
    filefunctions.delete_dir(paths.directory)
    filefunctions.make_sure_dir_exists(paths.directory)

    # set paths
    paths.extractor_path = os.path.join(os.getcwd(), 'libs', 'APICallExtractor.jar')
    paths.parser_path = os.path.join(os.getcwd(), 'libs', 'srcml', 'srcml')
    paths.apted_path = os.path.join(os.getcwd(), 'libs', 'APTED.jar')
    paths.beautifier_path = os.path.join(os.getcwd(), 'libs', 'astyle', 'astyle')

    paths.client_dir_path = os.path.join(os.getcwd(), 'data', 'dataset', 'source', 'client_files', dataset)
    paths.example_dir_path = os.path.join(os.getcwd(), 'data', 'dataset', 'source', 'example_files', dataset)
    paths.arff_file_path = os.path.join(os.getcwd(), 'results', dataset, dataset + '.arff')
    paths.namespace_dir_path = os.path.join(os.getcwd(), 'results', dataset, 'namespaces/')
    namespace_dir_class_path = os.path.join(paths.namespace_dir_path, 'class')
    namespace_dir_method_path = os.path.join(paths.namespace_dir_path, 'method')

    filefunctions.delete_dir(paths.namespace_dir_path)
    filefunctions.make_sure_dir_exists(paths.namespace_dir_path)
    filefunctions.make_sure_dir_exists(namespace_dir_class_path)
    filefunctions.make_sure_dir_exists(namespace_dir_method_path)

    return paths


class Paths:
    def __init__(self):
        self.directory = None
        self.extractor_path = None
        self.parser_path = None
        self.apted_path = None
        self.beautifier_path = None
        self.client_dir_path = None
        self.arff_file_path = None
        self.example_dir_path = None
        self.namespace_dir_path = None
