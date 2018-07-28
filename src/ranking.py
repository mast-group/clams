import os
from shutil import copyfile

from src.helper.filefunctions import make_sure_dir_exists
from src.helper.sequences_metrics import is_subseq


class Ranker:
    def __init__(self, res_dir, snippets_map, calls):
        """
        :type res_dir: str
        :param res_dir: the directory where the results of the current session are stored
        :type snippets_map: dictionary
        :param snippets_map: contains information about the mined snippets
        :type calls: list
        :param calls: the original list of API calls
        """
        self.res_dir = res_dir
        self.medoids_map = snippets_map
        self.calls = calls
        self.snippets_rank = []

    def rank_snippets(self):
        """
        Ranks mined snippets based on their support in the original dataset. We claim that a mined snippet is support by
        a file in the original dataset, if the latter's API call sequence is a super-sequence of the first's sequence.
        """
        snippets_info = []
        for key, value in self.medoids_map.iteritems():
            name = str(key) + '_' + value[0]['filename']
            support = 0
            seq1 = value[0]['calls']
            for seq2 in self.calls:
                if is_subseq(seq1, seq2):
                    support += 1
            snippets_info.append({'name': name, 'support': support, 'calls': value[0]['calls']})
        self.snippets_rank = sorted(snippets_info, key=lambda k: k['support'], reverse=True)

    def copy_ranked(self):
        """
        Copies the mined snippets in a new directory, naming them appropriately; their name indicates their position in
        the ranked list
        """
        medoid_dir = os.path.join(self.res_dir, 'medoids')
        ranked_dir = os.path.join(self.res_dir, 'ranked')
        make_sure_dir_exists(ranked_dir)
        name_cnt = -1
        for v in self.snippets_rank:
            name_cnt += 1
            name_split = v['name'].split('_', 1)
            medoid_path = os.path.join(medoid_dir, name_split[0], name_split[1][:-4] + '.java')
            ranked_path = os.path.join(ranked_dir, str(name_cnt) + '.java')
            if os.path.isfile(medoid_path):
                copyfile(medoid_path, ranked_path)
