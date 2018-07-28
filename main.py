import os
import sys
sys.path.insert(0, os.path.pardir)
import time

from mappings import projects_map
import src as summariser


def main():
    start_t = time.time()

    print "Setting up project..."
    paths = summariser.initialise.set_up_project()
    print "Ready to run new session...\n"

    for dataset in projects_map:
        print "Processing " + dataset + "..."
        paths = summariser.initialise.set_up_dataset(paths, dataset)

        print "Extracting API call sequences..."
        summariser.process_caller.extract_sequences(dataset, paths)
        print "API calls have been extracted successfully...\n"

        print "Loading dataset..."
        org_caller_file, org_caller_package, org_callers, org_calls = summariser.filefunctions.load_arff(
            paths.arff_file_path, omit=8)
        print "Dataset loaded!\n"

        print "Preprocessing data..."
        params_pre = {'metric': 'lcs', 'remove_singletons': False, 'remove_pseudo_singletons': False,
                      'remove_unique': False,
                      'call_name': '.*'}
        callers_file, callers_package, callers, calls, dist_mat, non_identical = \
            summariser.process_caller.preprocess_data(
                org_caller_file,
                org_caller_package,
                org_callers, org_calls,
                params_pre)
        print "Data preprocessing has been completely successfully!\n"

        print "Extracting files' ASTs..."
        ast_extractor = summariser.process_caller.extract_asts(callers, calls, paths.directory, paths.client_dir_path, paths.parser_path)
        print "ASTs have been extracted successfully!\n"

        print "Mapping callers to source files..."
        callers_info = summariser.mapper.get_callers_info(callers_file, callers_package, callers)
        summariser.filefunctions.write_json(paths.directory, 'callers_info', callers_info)
        print "Mapping completed successfully!\n"

        print "Extracting methods' ASTs..."
        ast_extractor.create_methods_xml(callers_info)
        print "Methods' ASTs are now stored in files!\n"

        print "Clustering sequences..."
        params_clust = {'algorithm': 'hdbscan', 'params': {'min_cluster_size': 2, 'min_samples': 2, 'metric': 'precomputed'}}
        clusterer = summariser.process_caller.cluster_sequences(callers, calls, paths.directory, dist_mat, params_clust)
        print "Clustering results are now stored in file!\n"

        print "Postprocessing sequences..."
        params_post = {'mode': 'identical', 'center': 'medoid', 'n': 5}
        top_files = summariser.postprocessing.get_top_callers(clusterer, params=params_post)
        print "Postprocessing completed successfully!\n"

        print "Writing top results to file..."
        summariser.filefunctions.write_json(paths.directory, 'top_files', top_files)
        print "Top results are now stored in file!\n"

        print "Generating snippets..."
        params_pat = {'summarise': True, 'resolve_types': True, 'remove_non_api': True}
        pattern_extractor = summariser.process_caller.generate_snippets(callers, callers_info, calls, paths.directory,
                                                                                    ast_extractor, top_files, params_pat)
        print "Generated snippets are now stored in files!\n"

        print "Selecting snippets..."
        snippet_selector = summariser.process_caller.select_snippets(clusterer, paths.directory, paths.parser_path, paths.apted_path,
                                                                                 pattern_extractor)
        print "Selected snippets are now stored in files!\n"

        print "Beautifying results..."
        summariser.beautify.beautify_examples(paths.beautifier_path, paths.directory)
        print "Results are really nice now!\n"

        print "Ranking results..."
        ranker = summariser.process_caller.rank_results(paths.directory, org_calls, snippet_selector)
        print "Ranked results are now stored in dir!\n"

        print "Writing top results to file..."
        summariser.filefunctions.write_json(paths.directory, 'ranked_files', ranker.snippets_rank)
        print "Clustering results are now stored in file!\n"

        print "Writing association between calls and results in file..."
        summariser.filefunctions.create_calls_files_map(paths.directory, 'ranked_files.json', 'calls_files_map.json')
        print "Association between calls and results is now stored in a file!\n"

        snippets_dir = os.path.join(paths.directory, 'ranked')
        print "No. mined files: " + str(summariser.filefunctions.count_dir_files(snippets_dir, '.java'))

        print dataset + " has been processed successfully!\n"

    print "Total script executed in %f seconds\n" % (time.time() - start_t)


if __name__ == '__main__':
    main()
