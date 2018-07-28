from Queue import heapq

import numpy as np


def get_top_callers(clusterer, params):
    """
    Returns the n callers with the smallest distance from their cluster's center.

    :type clusterer: ClusteringEngine Object
    :param clusterer: an instance of the Clustering engine that stores clustering results
    :type params: dictionary
    :param params: {'center','mode','n'}
    :return top_callers: a dictionary of sorted lists that contain the top callers of each cluster
    """
    top_callers = {}
    for c_id in clusterer.clusters_ids.keys():
        # get medoid's id in callers list for current cluster
        if params['center'] == 'medoid':
            medoid = clusterer.centers[c_id]
        # or get centroid coords
        elif params['center'] == 'centroid':
            centroid = clusterer.centers_l[int(c_id)]
        else:
            raise NotImplementedError
        tops_cluster = []

        if params['mode'] == 'identical':
            for m in clusterer.clusters_ids[c_id]:
                if clusterer.dist_mat[medoid][int(m)] == 0.0:
                    tops_cluster.append({'dist': 0.0, 'caller': clusterer.callers[int(m)], 'id': int(m)})
                    if len(tops_cluster) == params['n']:
                        break
            top_callers[c_id] = tops_cluster
        elif params['mode'] == 'nearest':
            for m in clusterer.clusters_ids[c_id]:
            # the negative sign is used in order to to convert heapq to min heap
                if params['center'] == 'medoid':
                    neg_dist = -clusterer.dist_mat[medoid][int(m)]
                elif params['center'] == 'centroid':
                    neg_dist = -np.linalg.norm(clusterer.f_vector[int(m)]-centroid)
                else:
                    raise NotImplementedError
                if len(tops_cluster) < params['n']:
                    heapq.heappush(tops_cluster, (neg_dist, int(m)))
                elif neg_dist > tops_cluster[0][0]:
                    heapq.heapreplace(tops_cluster, (neg_dist, int(m)))
            top_callers[c_id] = []
            for (dist, caller_id) in reversed(heapq.nsmallest(params['n'], tops_cluster)):
                caller = clusterer.callers[int(caller_id)]
                top_callers[c_id].append({'dist':-dist, 'caller':caller, 'id':caller_id})

    return top_callers
