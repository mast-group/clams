from __future__ import division

import copy
import random

import numpy as np


class KMedoids:
    """
    Performs clustering using the k-medoids algorithm. Results are stored in self.clusters. Implementation based on:
    Bauckhage, C. (2015). Numpy/scipy Recipes for Data Science: k-Medoids Clustering. Technical Report, University
    of Bonn.

    :type n_clusters: int
    :param n_clusters: the number of clusters to be created
    :type max_iter: int
    :param max_iter: the maximum number of iterations
    :type init: string
    :param init: ['k-medoids++','random',list]
    :type criterion: dictionary
    :param criterion: {'medoids', 'members'}
    """

    def __init__(self, n_clusters, max_iter, init, criterion):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.init = init
        self.criterion = criterion

    def fit(self, X):
        """
        Compute k-medoids clustering.

        :type X: numpy array
        :param X: the distance matrix to be used
        :return:
        """
        self.cluster_centers_, self.labels_ = k_medoids(X, n_clusters=self.n_clusters, init=self.init,
                                                        max_iter=self.max_iter, criterion=self.criterion)
        return self


def k_medoids(X, n_clusters, init, max_iter, criterion):
    """
    The main function of the k-medoids algorithm.

    :type X: numpy array
    :param X: the distance matrix to be used
    :type n_clusters: int
    :param n_clusters: the number of clusters to be created
    :type init: string
    :param init: ['k-medoids++','random',list]
    :type max_iter: int
    :param max_iter: the maximum number of iterations
    :type criterion: dictionary
    :param criterion: {'medoids', 'members'}
    :return: medoid_ids: the ids of the medoids
    :return labels: the ids of the clusters to which the data points have been assigned

    """

    m, n = X.shape
    # initialize k medoids
    if init == 'random':
        random.seed(0)
        b = np.ascontiguousarray(X).view(np.dtype((np.void, X.dtype.itemsize * X.shape[1])))
        _, idx = np.unique(b, return_index=True)
        medoid_ids = np.sort(random.sample(idx, n_clusters))
    elif init == 'k-medoids++':
        medoid_ids = np.sort(init_centers(X, n_clusters))
    elif type(init) is list:
        medoid_ids = np.sort(init)
    else:
        raise NotImplementedError

    # create a copy of the array of medoid indices
    medoid_ids_new = np.copy(medoid_ids)
    # initialize a dictionary to represent clusters
    clusters_ids = {}
    clusters_ids_new = {}

    for t in range(max_iter):
        # determine clusters, i.e. arrays of data indices
        clusters_ids_new = kmedoids_update_clusters(X, n_clusters, medoid_ids_new, clusters_ids_new)

        # update medoids
        medoid_ids_new = kmedoids_update_medoids(X, n_clusters, medoid_ids_new, clusters_ids_new)

        medoid_ids_new = np.sort(medoid_ids_new)

        # check for convergence
        if criterion == 'medoids':
            if np.array_equal(medoid_ids, medoid_ids_new):
                break
        elif criterion == 'members':
            if t > 0:
                arrays_equal = (np.array_equal(clusters_ids[key], clusters_ids_new[key]) for key in
                                clusters_ids.keys())
                if all(arrays_equal):
                    break
        else:
            raise NotImplementedError

        clusters_ids = copy.deepcopy(clusters_ids_new)
        medoid_ids = np.copy(medoid_ids_new)

    else:
        clusters_ids_new = kmedoids_update_clusters(X, n_clusters, medoid_ids_new, clusters_ids_new)

    labels = form_labels(X, clusters_ids_new)
    return medoid_ids, labels


def form_labels(X, clusters_ids):
    """
    Fills the list of labels.

    :type X: numpy array
    :param X: the distance matrix to be used
    :type clusters_ids: dict
    :param clusters_ids: clusters results, stored in dictionary
    :return labels: the ids of the clusters to which the data points have been assigned
    """
    labels = np.zeros(X.shape[0], dtype=int)
    for key, value in clusters_ids.iteritems():
        for idx in value:
            labels[idx] = int(key)
    return labels


def dist_from_centers(X, medoids):
    """
    Computes distances between points and medoids.

    :type X: numpy array
    :param X: the distance matrix to be used
    :type medoids: list
    :param medoids: the medoids generated so far
    :return D:the distance matrix used in the k++ initialisation
    """
    D = np.array([min([X[i, c] for c in medoids]) for i in range(X.shape[0])])
    return D


def choose_next_center(X):
    """
    Choose next medoid randomly based on the probability distribution D / D.sum().

    :type X: numpy array
    :param X: the distance matrix to be used
    :return ind: the index of the selected medoid
    """
    probs = X / X.sum()
    cumprobs = probs.cumsum()
    random.seed(0)
    r = random.random()
    ind = np.where(cumprobs >= r)[0][0]
    return ind


def init_centers(X, n_clusters):
    """
    Initialise medoids using the k++ technique.

    :type X: numpy array
    :param X: the distance matrix to be used
    :type n_clusters: int
    :param n_clusters: the number of clusters
    :return medoids: medoids' indices
    """
    # choose first medoid randomly
    # mu = random.sample(range(len(self.callers)), 1)
    medoids = [0]
    while len(medoids) < n_clusters:
        dist_mat = dist_from_centers(X, medoids)
        medoids.append(choose_next_center(dist_mat))
    return medoids


def kmedoids_update_clusters(X, n_clusters, medoid_ids, clusters_ids):
    """
    Updates clusters on each k-medoids iteration.

    :type X: numpy array
    :param X: the distance matrix to be used
    :type n_clusters: int
    :param n_clusters: the number of clusters
    :type medoid_ids: array like
    :param medoid_ids: the ids of the medoids
    :type clusters_ids: dict
    :param clusters_ids: clusters results, stored in dictionary
    :return clusters_ids: updated clusters
    """
    # determine clusters, i.e. arrays of data indices
    # argmin returns the cluster id of the closest medoid
    J = np.argmin(X[:, medoid_ids], axis=1)
    # J[medoid_ids] = range(n_clusters)

    for kappa in range(n_clusters):
        clusters_ids[kappa] = np.where(J == kappa)[0]

    return clusters_ids


def kmedoids_update_medoids(X, n_clusters, medoid_ids, clusters_ids):
    """
    Updates medoids on each k-medoids iteration.

    :type X: numpy array
    :param X: the distance matrix to be used
    :type n_clusters: int
    :param n_clusters: the number of clusters
    :type medoid_ids: array like
    :param medoid_ids: the ids of the medoids
    :type clusters_ids: dict
    :param clusters_ids: clusters results, stored in dictionary
    :return medoid_ids: updated medoids
    """
    # update medoids
    for kappa in range(n_clusters):
        J = np.mean(X[np.ix_(clusters_ids[kappa], clusters_ids[kappa])], axis=1)
        j = np.argmin(J)
        medoid_ids[kappa] = clusters_ids[kappa][j]

    return medoid_ids
