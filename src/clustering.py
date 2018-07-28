import numpy as np
from hdbscan import HDBSCAN
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.cluster import MeanShift
from src.helper.sequences_metrics import is_subseq

from kmedoids import KMedoids


class ClusteringEngine:
    """
    Clusters the API call sequences using one of the clustering algorithms that have been implemented/integrated into
    the system.
    """

    def __init__(self, callers, calls, dist_mat):
        """
        :type callers: list
        :param callers: a list of caller methods
        :type calls: list of lists
        :param calls: a list of method call sequences
        :type dist_mat: numpy array
        :param dist_mat: the distance matrix
        """
        self.callers = callers
        self.calls = calls
        self.dist_mat = dist_mat
        self.clusters = {}
        self.clusters_ids = {}
        self.labels = {}
        self.labels_l = np.zeros(len(self.callers), dtype=np.int)
        self.centers = {}
        self.centers_l = []
        self.f_vector = np.zeros((len(self.callers), 2))

    def restart(self):
        """
        Clears clustering engine data.
        """
        self.clusters = {}
        self.clusters_ids = {}
        self.labels = {}
        self.labels_l = np.zeros(len(self.callers), dtype=np.int)
        self.centers = {}
        self.centers_l = []

    def run_dbscan(self, params):
        """
        Performs clustering using the DBSCAN algorithm.

        :type params: dictionary
        :param params: {'eps','min_samples','metric','algorithm'}
        """
        if params['metric'] == 'precomputed':
            db = DBSCAN(eps=params['eps'], min_samples=params['min_samples'], metric=params['metric'],
                        algorithm=params['algorithm']).fit(self.dist_mat)
        else:
            db = DBSCAN(eps=params['eps'], min_samples=params['min_samples'], metric=params['metric'],
                        algorithm=params['algorithm']).fit(self.f_vector)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        self.labels_l = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        self.n_clusters_ = len(set(self.labels_l)) - (1 if -1 in self.labels_l else 0)
        print('Estimated number of clusters: %d' % self.n_clusters_)

        self.form_dbscan_results()

    def run_hdbscan(self, params):
        """
        Performs clustering using the HDBSCAN algorithm.

        :type params: dictionary
        :param params: {'min_cluster_size','min_samples','metric'}
        """
        if params['metric'] == 'precomputed':
            hdb = HDBSCAN(min_cluster_size=params['min_cluster_size'], min_samples=params['min_samples'],
                          metric=params['metric']).fit(self.dist_mat)
        else:
            hdb = HDBSCAN(min_cluster_size=params['min_cluster_size'], min_samples=params['min_samples'],
                          metric=params['metric']).fit(self.f_vector)
        self.labels_l = hdb.labels_

        # Number of clusters in labels, ignoring noise if present.
        self.n_clusters_ = len(set(self.labels_l)) - (1 if -1 in self.labels_l else 0)
        print('Estimated number of clusters: %d' % self.n_clusters_)

        self.form_dbscan_results()

    def run_kmedoids(self, params):
        """
        Performs clustering using the k-medoids algorithm.

        :type params: dictionary
        :param params: {'k','t_max','init','criterion'}
        """
        self.n_clusters_ = params['k']
        kmedoids = KMedoids(n_clusters=params['k'], max_iter=params['t_max'], init=params['init'],
                            criterion=params['criterion']).fit(self.dist_mat)
        self.centers_l = kmedoids.cluster_centers_
        self.labels_l = kmedoids.labels_
        self.form_kmedoids_results()

    def run_kmeans(self, params):
        """
        Runs the k-means++ algorithm for the feature vector.

        :type params: int
        :param params: {'k'}
        """
        self.n_clusters_ = params['k']
        kmeans = KMeans(n_clusters=params['k']).fit(self.f_vector)
        self.inertia_ = kmeans.inertia_
        self.labels_l = kmeans.labels_
        self.centers_l = kmeans.cluster_centers_
        self.form_kmedoids_results()

    def run_meanshift(self):
        """
        Runs the Mean Shift algorithm. No parameters used in this algorithm.
        """
        res = MeanShift().fit(self.f_vector)
        self.labels_l = res.labels_
        self.centers_l = res.cluster_centers_
        labels_unique = np.unique(self.labels_l)
        self.n_clusters_ = len(labels_unique)

        print("number of estimated clusters : %d" % self.n_clusters_)
        self.form_dbscan_results()

    def run_overlapping(self):
        """
        Runs a naive overlapping algorithm, which creates a cluster for each distinct sequence, and assigns any of
        its (super)sequences to the cluster.
        """
        self.cluster_seqs = {}
        self.n_clusters_ = -1
        for i in range(len(self.calls)):
            if self.calls[i] not in self.cluster_seqs.values():
                l_ids = set()
                l_callers = set()
                for j in range(len(self.calls)):
                    if is_subseq(self.calls[i], self.calls[j]):
                        l_ids.add(j)
                        l_callers.add(self.callers[j])
                if len(l_callers) > 0:
                    self.n_clusters_ += 1
                    self.centers[str(self.n_clusters_)] = i
                    self.centers_l.append(i)
                    self.cluster_seqs[str(self.n_clusters_)] = self.calls[i]
                    self.clusters_ids[str(self.n_clusters_)] = list(l_ids)
                    self.clusters[str(self.n_clusters_)] = list(l_callers)

    def form_dbscan_results(self):
        """
        Fills self.clusters and self.labels based on labels and callers data. Used from DBSCAN and HDBSCAN..
        """
        for i in range(len(self.labels_l)):
            self.labels[self.callers[i]] = self.labels_l[i]
            if str(self.labels_l[i]) in self.clusters:
                self.clusters[str(self.labels_l[i])].append(self.callers[i])
                self.clusters_ids[str(self.labels_l[i])].append(i)
            else:
                # if self.labels_l[i] != -1:
                self.centers[str(self.labels_l[i])] = i
                self.clusters[str(self.labels_l[i])] = [self.callers[i]]
                self.clusters_ids[str(self.labels_l[i])] = [i]

        # find clustering's centers, using the data points' intra-cluster support
        for key, value in self.clusters_ids.iteritems():
            max_id = value[0]
            max_support = 1
            for v in value:
                support = 0
                for v1 in value:
                    if self.dist_mat[v, v1] == 1.0:
                        support += 1
                if support > max_support:
                    max_support = support
                    max_id = v
            self.centers[key] = max_id

    def form_kmedoids_results(self):
        """
        Fills self.clusters and self.labels based on labels and callers data.
        """

        for i in range(len(self.labels_l)):
            self.labels[self.callers[i]] = self.labels_l[i]
            if str(self.labels_l[i]) in self.clusters:
                self.clusters[str(self.labels_l[i])].append(self.callers[i])
                self.clusters_ids[str(self.labels_l[i])].append(i)
            else:
                self.clusters[str(self.labels_l[i])] = [self.callers[i]]
                self.clusters_ids[str(self.labels_l[i])] = [i]

        for i in range(self.n_clusters_):
            self.centers[str(i)] = self.centers_l[i]

    def perform_clustering(self, algorithm, params):
        """
        Calls the appropriate clustering function.

        :type algorithm: string
        :param algorithm: ['k-medoids','dbscan','hdbscan','k-means','mean-shift','overlapping']
        :type params: dictionary
        :param params: the parameters used by the algorithm
        """
        if algorithm == 'k-medoids':
            self.run_kmedoids(params)
        elif algorithm == 'dbscan':
            self.run_dbscan(params)
        elif algorithm == 'hdbscan':
            self.run_hdbscan(params)
        elif algorithm == 'k-means':
            self.run_kmeans(params)
        elif algorithm == 'mean-shift':
            self.run_meanshift()
        elif algorithm == 'overlapping':
            self.run_overlapping()
        else:
            raise NotImplementedError
