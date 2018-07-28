from __future__ import division

import os
import time
from subprocess import Popen, PIPE, STDOUT

import numpy as np
from lxml import etree
from src.helper import filefunctions
from tqdm import tqdm


class SnippetSelector:
    def __init__(self, res_dir, apted_path, parser_path, clusters, snippets_name_id_map):
        """
        :type res_dir: str
        :param res_dir: the directory where the results of the current session are stored
        :type clusters: int
        :param clusters: the number of clusters
        :type snippets_name_id_map: dictionary
        :param snippets_name_id_map: a map between the snippets and its associated id, used to retrieve their API calls
        """
        self.res_dir = res_dir
        self.apted_path = apted_path
        self.clusters = clusters
        self.selected_snippets_map = {}
        self.snippets_name_id_map = snippets_name_id_map
        self.parser_path = parser_path

    def perform_snippet_selection(self):
        """
        Calls the appropriate functions to select the most representative snippet of each cluster.
        """
        self.find_representatives()
        filefunctions.write_json(self.res_dir, 'medoids_map', self.selected_snippets_map)
        self.snippets_source()

    def find_representatives(self):
        """
        Finds the most representative snippet for each cluster.This is the snippet with the most common structure among
        its clusters' top files, and can be found using the APTED tree edit distance.
        """
        patterns_dir = os.path.join(self.res_dir, 'patternFiles')
        for i in tqdm(range(self.clusters)):
            cluster_dir = os.path.join(patterns_dir, str(i))
            if os.path.isdir(cluster_dir):
                patterns = os.listdir(cluster_dir)
                sim_mat = self.compute_distances(patterns, i)
                sum_lev = np.sum(sim_mat, axis=1)
                minindex = sum_lev.argmin()
                medoid_calls = self.snippets_name_id_map[str(i)][patterns[minindex]]
                self.selected_snippets_map[str(i)] = [{'filename': patterns[minindex], 'calls': medoid_calls}]

    def compute_distances(self, patterns, cluster_id):
        """
        Computes a similarity matrix for the xml files, based on string distance metrics.

        :type patterns: list of str
        :param patterns: a list of xml filenames of a cluster's generated snippets
        :type cluster_id: int
        :param cluster_id: a cluster id
        :return sim_mat: the similarity matrix
        """
        dist_mat = np.zeros((len(patterns), len(patterns)))
        for i in range(len(patterns)):
            for j in range(i + 1):
                filepath1 = os.path.join(self.res_dir, 'patternFiles', str(cluster_id), patterns[i])
                filepath2 = os.path.join(self.res_dir, 'patternFiles', str(cluster_id), patterns[j])
                root1 = etree.parse(filepath1).getroot()
                root2 = etree.parse(filepath2).getroot()
                trans1_l = []
                trans2_l = []
                # form transactions to be used by the APTED tool
                self.form_transaction(root1, trans1_l)
                self.form_transaction(root2, trans2_l)
                trans1_s = ''.join(trans1_l)
                trans2_s = ''.join(trans2_l)
                p = Popen(['java', '-jar', self.apted_path, '-t', trans1_s, trans2_s], stdout=PIPE, stdin=PIPE,
                          stderr=PIPE)
                dist = p.communicate()[0].strip()
                dist_mat[i][j] = float(dist)
                dist_mat[j][i] = dist_mat[i][j]
        return dist_mat

    def form_transaction(self, root, trans):
        """
        Forms a transaction, in the form used by the APTED tool, by recursively traversing the given tree.

        :type root: Element
        :param root: the root of the xml document
        :type trans: list
        :param trans: the elements of the transaction so far
        """
        tag = root.tag.strip().split('}', 1)[1]
        if tag != '':
            trans.append('{')
            trans.append(tag)
        for elem in root.getchildren():
            self.form_transaction(elem, trans)
        trans.append('}')

    def snippets_source(self):
        """
        Retrieves the source code for each of the selected snippets. It transforms their associated xml files back to
        Java source code, using the srcml tool.
        """
        medoids_dir = os.path.join(self.res_dir, 'medoids')
        filefunctions.make_sure_dir_exists(medoids_dir)
        time.sleep(2)
        for key, value in tqdm(self.selected_snippets_map.iteritems()):
            filefunctions.make_sure_dir_exists(os.path.join(medoids_dir, str(key)))
            for medoid in value:
                medoid_path = os.path.join(self.res_dir, 'patternFiles', str(key), medoid['filename'])
                filepath = os.path.join(medoids_dir, str(key), medoid['filename'][:-4] + '.java')
                p = Popen([self.parser_path, medoid_path, '-o', filepath],
                          stdout=PIPE, stderr=STDOUT)
                p.communicate()[0]
