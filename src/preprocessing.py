import re

import numpy as np
from sklearn import manifold
from src.helper import sequences_metrics
from tqdm import tqdm


class Preprocessor:
    def __init__(self, callers_file, callers_package, callers, calls):
        """
        :param callers_file:
        :param callers_package:
        :param callers: a list of caller methods
        :param calls: a list of method call sequences
        """
        self.callers_file = callers_file
        self.callers_package = callers_package
        self.callers = callers
        self.calls = calls

    def perform_preprocessing(self, mode, params):
        """
        Calls the appropriate functions to preprocess the data.

        :type mode: string
        :param mode: ['vector', 'distance']
        :type params: dictionary
        :param params: {'metric','remove_singletons','remove_pseudo_singletons','remove_unique'}
        """
        params_clean = {'remove_singletons': params['remove_singletons'],
                        'remove_pseudo_singletons': params['remove_pseudo_singletons'],
                        'call_name': params['call_name']}
        self.clean_data(params_clean)
        if mode == 'vector':
            self.create_vector()
        elif mode == 'distance':
            dist_func = self.get_dist_func(params['metric'])
            self.compute_similarity(dist_func)
            if params['remove_unique']:
                self.remove_outliers()
        else:
            raise NotImplementedError

    def clean_data(self, params):
        """
        Cleans the dataset, based on the specified option. Note that the 'remove_pseudo_singletons' option should be
        combined with the 'remove_singletons' one.

        :type params: dictionary
        :param params: {'remove_singletons','remove_pseudo_singletons', 'call_name'}
        """
        upd_callers_file = []
        upd_callers_package = []
        upd_callers = []
        upd_calls = []

        reg = params['call_name']
        pattern = re.compile(reg)

        for i in range(len(self.calls)):
            # remove duplicate callers and sequences with single/identical API calls (includes singleton sequences)
            if self.callers[i] not in upd_callers:
                # exclude api calls that are not included in services
                api_calls = []
                for api_call in self.calls[i]:
                    class_filename = '.'.join(api_call.split('.')[-2:])
                    if re.search(pattern, class_filename):
                        api_calls.append(api_call)

                if params['remove_singletons']:
                    if params['remove_pseudo_singletons']:
                        if self.calls[i].count(self.calls[i][0]) != len(self.calls[i]):
                            upd_callers_file.append(self.callers_file[i])
                            upd_callers_package.append(self.callers_package[i])
                            upd_callers.append(self.callers[i])
                            upd_calls.append(self.calls[i])
                    else:
                        if self.calls[i] > 1:
                            upd_callers_file.append(self.callers_file[i])
                            upd_callers_package.append(self.callers_package[i])
                            upd_callers.append(self.callers[i])
                            upd_calls.append(self.calls[i])
                else:
                    if len(api_calls) > 0:
                        upd_callers_file.append(self.callers_file[i])
                        upd_callers_package.append(self.callers_package[i])
                        upd_callers.append(self.callers[i])
                        upd_calls.append(api_calls)
        self.callers_file = upd_callers_file
        self.callers_package = upd_callers_package
        self.callers = upd_callers
        self.calls = upd_calls

    def get_dist_func(self, metric):
        """
        Gets an instance of the function that will be used for computing sequence similarity.

        :type metric: string
        :param metric: ['lcs', 'lcs-mod', 'lcs-min', 'lcs-ext', 'jaccard', 'jaccard-min', 'gestalt', 'seqsim',
        'levenshtein']
        """
        if metric == 'lcs':
            dist_func = getattr(sequences_metrics, 'lcs')
        elif metric == 'lcs-mod':
            dist_func = getattr(sequences_metrics, 'lcs_mod')
        elif metric == 'lcs-min':
            dist_func = getattr(sequences_metrics, 'lcs_min')
        elif metric == 'lcs-ext':
            dist_func = getattr(sequences_metrics, 'lcs_ext')
        elif metric == 'jaccard':
            dist_func = getattr(sequences_metrics, 'jaccard')
        elif metric == 'jaccard-min':
            dist_func = getattr(sequences_metrics, 'jaccard_min')
        elif metric == 'gestalt':
            dist_func = getattr(sequences_metrics, 'gestalt')
        elif metric == 'seqsim':
            dist_func = getattr(sequences_metrics, 'seqsim')
        elif metric == 'levenshtein':
            dist_func = getattr(sequences_metrics, 'levenshtein')
        else:
            raise NotImplementedError

        return dist_func

    def compute_similarity(self, dist_func):
        """
        Creates a distance matrix based on the computed similarities between sequences (API calls).

        :type dist_func: function
        :param dist_func: an instance of the distance function to be used
        """
        self.dist_mat = np.zeros((len(self.calls), len(self.calls)))
        for i in tqdm(range(len(self.calls))):
            for j in range(i + 1):
                self.dist_mat[i][j] = dist_func(self.calls[i], self.calls[j])
                self.dist_mat[j][i] = self.dist_mat[i][j]

    def remove_outliers(self):
        """
        Currently removes sequences that are unique. It makes use of the distance matrix, for efficiency reasons.
        This could be easily avoided by a brute-force solution.
        """
        ind_to_remove = []
        for i in range(len(self.callers)):
            if np.count_nonzero(self.dist_mat[i] == 0.0) == 1:
                ind_to_remove.append(i)
        self.dist_mat = np.delete(self.dist_mat, ind_to_remove, axis=0)
        self.dist_mat = np.delete(self.dist_mat, ind_to_remove, axis=1)
        for i in reversed(ind_to_remove):
            self.callers_file.pop(i)
            self.callers_package.pop(i)
            self.callers.pop(i)
            self.calls.pop(i)
        print 'Data points after removing outliers: ' + str(len(self.callers))

    def dist_to_vec(self, params):
        """
        Generates a feature vector given a distance matrix and based on the t-SNE algorithm.

        :type params: dictionary
        :param params: {'n_components','perplexity','random_state'}
        """
        model = manifold.TSNE(n_components=params['n_components'], perplexity=params['perplexity'],
                              metric="precomputed", random_state=params['random_state'])
        np.set_printoptions(suppress=True)
        self.f_vector = model.fit_transform(self.dist_mat)

    def create_vector(self):
        """
        Generate feature vectors, using the API method calls as features. THis does not take into account the order in
        which the API methods are invoked.
        """
        self.calls_set = set()
        for calls in self.calls:
            self.calls_set.update(calls)
        self.calls_set = list(self.calls_set)
        self.f_vector = np.zeros((len(self.callers), len(self.calls_set)))
        print len(self.f_vector)
        for caller_id in range(len(self.callers)):
            for call_id in range(len(self.calls_set)):
                if self.calls_set[int(call_id)] in self.calls[int(caller_id)]:
                    self.f_vector[int(caller_id)][int(call_id)] = 1
        print 'Non-zero elements:' + str(np.count_nonzero(self.f_vector))

    def freq_idx(self):
        seen_el = []
        seen_idx = []
        for i in range(len(self.calls)):
            for j in range(i + 1, len(self.calls)):
                if self.calls[j] == self.calls[i] and self.calls[j] not in seen_el:
                    seen_el.append(self.calls[j])
                    seen_idx.append(j)
        return seen_idx

    def non_identical_seqs(self):
        """
        Selects all the non_identical sequences.
        """
        non_identical_calls = []
        for call in self.calls:
            if call not in non_identical_calls:
                non_identical_calls.append(call)
        return non_identical_calls
