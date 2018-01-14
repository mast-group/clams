import os
import time

import apisummariser as summariser


def main():
    dataset = 'twitter4j'
    package_name = 'twitter4j'

    startt = time.time()
    print "Setting up project..."
    paths = summariser.initialise.set_up(dataset)
    print "Ready to run new session...\n"

    print "Extracting API call sequences..."
    params_call_extr = {'lib-dir': paths.client_dir_path, 'lib-name': dataset, 'package-name': package_name,
                        'out-file': paths.arff_file_path, 'resolve-wildcards': True,
                        'example-dir': paths.example_dir_path,
                        'namespace-dir': paths.namespace_dir_path}
    api_call_extractor = summariser.APICallExtractor(paths.extractor_path)
    api_call_extractor.extract(params_call_extr)
    print "API calls have been extracted successfully...\n"

    print "Loading dataset..."
    org_caller_file, org_caller_package, org_callers, org_calls = summariser.filefunctions.load_arff(
        paths.arff_file_path, omit=8)
    print "Dataset loaded!\n"

    print "Preprocessing data..."
    preprocessor = summariser.Preprocessor(org_caller_file, org_caller_package, org_callers, org_calls)
    params_pre = {'metric': 'lcs', 'remove_singletons': True, 'remove_pseudo_singletons': True, 'remove_unique': False}
    preprocessor.perform_preprocessing(mode='distance', params=params_pre)
    callers_file, callers_package, callers, calls, dist_mat = preprocessor.callers_file, preprocessor.callers_package, \
                                                              preprocessor.callers, preprocessor.calls, preprocessor.dist_mat
    # use this as the k value, for a naive clustering
    # non_identical = len(preprocessor.non_identical_seqs())
    print "Data preprocessing has been completely successfully!\n"

    print "Extracting files' ASTs..."
    src_dir = paths.client_dir_path
    dst_dir = os.path.join(paths.directory, 'srcFiles')
    summariser.filefunctions.copy_dir_files(src_dir, dst_dir)
    parser = summariser.ASTExtractor(paths.directory, callers, calls, paths.parser_path)
    parser.extract_asts()
    print "ASTs have been extracted successfully!\n"

    print "Mapping callers to source files..."
    callers_info = summariser.mapper.get_callers_info(callers_file, callers_package, callers, paths.directory)
    summariser.filefunctions.write_json(paths.directory, 'callers_info', callers_info)
    print "Mapping completed successfully!\n"

    print "Extracting methods' ASTs..."
    parser.create_methods_xml(callers_info)
    print "Methods' ASTs are now stored in files!\n"

    print "Clustering sequences..."
    startc = time.time()
    clusterer = summariser.ClusteringEngine(callers, calls, dist_mat)

    '''params_clust = {'k': 110, 't_max': 100, 'init': 'k-medoids++', 'criterion': 'medoids'}
    clusterer.perform_clustering(algorithm='k-medoids', params=params_clust)'''

    params_clust = {'min_cluster_size': 2, 'min_samples': 2, 'metric': 'precomputed'}
    clusterer.perform_clustering(algorithm='hdbscan',
                                 params=params_clust)

    print "Clustering executed in %f seconds\n" % (time.time() - startc)

    print "Writing clustering results to file..."
    summariser.filefunctions.write_json(paths.directory, 'clusters', clusterer.clusters)
    print "Clustering results are now stored in file!\n"

    params_post = {'mode': 'identical', 'center': 'medoid', 'n': 5}
    top_files = summariser.postprocessing.get_top_callers(clusterer, params=params_post)

    print "Writing top results to file..."
    summariser.filefunctions.write_json(paths.directory, 'top_files', top_files)
    print "Top results are now stored in file!\n"

    print "Generating snippets..."
    params_pat = {'summarise': True, 'resolve_types': True, 'remove_non_api': True}
    pattern_extractor = summariser.SnippetGenerator(paths.directory, top_files, callers_info, callers, calls,
                                                    parser.class_vars)
    pattern_extractor.perform_snippet_generation(params=params_pat)
    print "Generated snippets are now stored in files!\n"

    print "Selecting snippets..."
    snippet_selector = summariser.SnippetSelector(paths.directory, paths.apted_path, clusterer.n_clusters_,
                                                  pattern_extractor.patterns_name_id_map)
    snippet_selector.perform_snippet_selection()
    print "Selected snippets are now stored in files!\n"

    print "Beautifying results..."
    summariser.beautify.beautify_examples(paths.beautifier_path, paths.directory)
    print "Results are really nice now!\n"

    print "Ranking results..."
    ranker = summariser.Ranker(paths.directory, snippet_selector.selected_snippets_map, org_calls)
    ranker.rank_snippets()
    ranker.copy_ranked()
    print "Ranked results are now stored in dir!\n"

    print "Writing top results to file..."
    summariser.filefunctions.write_json(paths.directory, 'ranked_files', ranker.snippets_rank)
    print "Clustering results are now stored in file!\n"

    snippets_dir = os.path.join(paths.directory, 'ranked')
    print "No. mined files: " + str(summariser.filefunctions.count_dir_files(snippets_dir, '.java'))
    print "Total script executed in %f seconds\n" % (time.time() - startt)


if __name__ == '__main__':
    main()
