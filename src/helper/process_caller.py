import os
import time

from mappings import projects_map
import src as summariser


def remove_previous_session(directory):
    """
    Sets up the new session by removing previous session results.
    :param directory: directory where results are stored
    """
    summariser.filefunctions.delete_dir(directory)
    summariser.filefunctions.make_sure_dir_exists(directory)


def extract_sequences(dataset, paths):
    """
    Extracts the API call sequences by calling the APICallExtractor.
    :param dataset: the name of the dataset
    :param paths: paths instance
    """
    package_name = projects_map[dataset]['package']
    params_call_extr = {'lib-dir': paths.client_dir_path, 'lib-name': dataset, 'package-name': package_name,
                        'out-file': paths.arff_file_path, 'resolve-wildcards': True,
                        'example-dir': paths.example_dir_path,
                        'namespace-dir': paths.namespace_dir_path}
    api_call_extractor = summariser.APICallExtractor(paths.extractor_path)
    api_call_extractor.extract(params_call_extr)


def preprocess_data(org_caller_file, org_caller_package, org_callers, org_calls, params_pre):
    """
    Preprocesses/cleans data by calling the Preprocessor.
    :param org_caller_file: filename of the caller
    :param org_caller_package: package package name of the caller
    :param org_callers: a list of client methods (callers)
    :param org_calls: a list of API method called by the corresponding client method
    :param params_pre: preprocessing parameters
    :return callers_file: updated org_caller_file
    :return callers_package: updated org_caller_package
    :return callers: updated callers
    :return calls: updated org_calls
    :return dist_mat: distance matrix computed between the API call sequences
    :return non_identical: number of non-identical sequences

    """
    preprocessor = summariser.Preprocessor(org_caller_file, org_caller_package, org_callers, org_calls)
    preprocessor.perform_preprocessing(mode='distance', params=params_pre)
    callers_file, callers_package, callers, calls, dist_mat = \
        preprocessor.callers_file, preprocessor.callers_package, \
        preprocessor.callers, preprocessor.calls, preprocessor.dist_mat
    # use this as the k value, for a naive clustering
    non_identical = len(preprocessor.non_identical_seqs())
    return callers_file, callers_package, callers, calls, dist_mat, non_identical


def extract_asts(callers, calls, directory, lib_dir_path, parser_path):
    """
    Extracts files' ASTs by calling the ASTExtractor.
    :param callers: a list of client methods (callers)
    :param calls: a list of API method called by the corresponding client method
    :param directory: directory where results are stored
    :param lib_dir_path: diretory where data files are stored
    :param parser_path: parser's path
    :return: an instance of ASTExtractor
    """
    src_dir = lib_dir_path
    dst_dir = os.path.join(directory, 'srcFiles')
    summariser.filefunctions.copy_dir_files(src_dir, dst_dir)
    ast_extractor = summariser.ASTExtractor(directory, callers, calls, parser_path)
    ast_extractor.extract_asts()
    return ast_extractor


def cluster_sequences(callers, calls, directory, dist_mat, params_clust):
    """
    Clusters the API call call sequences by calling the ClusteringEngine.
    :param callers: a list of client methods (callers)
    :param calls: a list of API method called by the corresponding client method
    :param directory: directory where results are stored
    :param dist_mat: distance matrix computed between the API call sequences
    :param params_clust: {'algorithm': <algorithm>, 'params': {...}}
    :return: an instance of ClusteringEngine
    """
    start_c = time.time()
    clusterer = summariser.ClusteringEngine(callers, calls, dist_mat)
    clusterer.perform_clustering(algorithm=params_clust['algorithm'], params=params_clust['params'])
    print "Clustering executed in %f seconds\n" % (time.time() - start_c)
    print "Writing clustering results to file..."
    summariser.filefunctions.write_json(directory, 'clusters', clusterer.clusters)
    return clusterer


def generate_snippets(callers, callers_info, calls, directory, ast_extractor, top_files, params_pat):
    """
    Generates API usage examples by calling the SnippetGenerator.
    :param callers: a list of client methods (callers)
    :param callers_info: mapping between callers and source files
    :param calls: a list of API method called by the corresponding client method
    :param directory: directory where results are stored
    :param ast_extractor: an instance of ASTExtractor
    :param top_files: a dictionary of sorted lists that contain the top callers of each cluster
    :param params_pat: snippet generator parameters
    :return: an instance of SnippetGenerator
    """
    snippet_generator = summariser.SnippetGenerator(directory, top_files, callers_info, callers, calls,
                                                    ast_extractor.class_vars)
    snippet_generator.perform_snippet_generation(params=params_pat)
    return snippet_generator


def select_snippets(clusterer, directory, parser_path, apted_path, snippet_generator):
    """
    Selects the most representative API usage examples by calling the SnippetSelector.
    :param clusterer: an instance of ClusteringEngine
    :param directory: directory where results are stored
    :param parser_path: parser's path
    :param apted_path: APTED's path
    :param snippet_generator: an instance of SnippetGenerator
    :return: an instance of SnippetSelector
    """
    snippet_selector = summariser.SnippetSelector(directory, apted_path, parser_path, clusterer.n_clusters_,
                                                  snippet_generator.patterns_name_id_map)
    snippet_selector.perform_snippet_selection()
    return snippet_selector


def rank_results(directory, org_calls, snippet_selector):
    """
    Ranks results by calling the Ranker.
    :param directory: directory where results are stored
    :param org_calls: a list of API method called by the corresponding client method
    :param snippet_selector: an instance of SnippetSelector
    :return: an instance of Ranker
    """
    ranker = summariser.Ranker(directory, snippet_selector.selected_snippets_map, org_calls)
    ranker.rank_snippets()
    ranker.copy_ranked()
    return ranker
