from __future__ import division
from difflib import SequenceMatcher


def lcs_len(x, y):
    """
    Computes the length of the Longest Common Subsequence (LCS) between two lists using DP in O(nm).
    Implementation available on:
    https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_subsequence

    :type x: list of strings
    :param x: a sequence
    :type y: list of strings
    :param y: a sequence
    :return: the length of the LCS
    """
    m = len(x)
    n = len(y)

    C = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                C[i][j] = C[i - 1][j - 1] + 1
            else:
                C[i][j] = max(C[i][j - 1], C[i - 1][j])
    return C[m][n]


def lcs(seq1, seq2):
    """
    Computes the distance between two sequences using the formula below:

    D(X, Y) = 1 - (2 * LCS(|X|,|Y|) / (|X| + |Y|)),

    where LCS: the length of the Longest Common Subsequence between two sequences.

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    dist = 1 - (2 * lcs_len(seq1, seq2) / (len(seq1) + len(seq2)))

    return dist


def lcs_mod(seq1, seq2):
    """
    Computes the distance between two sequences using the formula below:

    D(X, Y) = (|X| + |Y| - 2 * LCS(|X|,|Y|) ) / (|X| + |Y|)),

    where LCS: the length of the Longest Common Subsequence between two sequences.

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    dist = (len(seq1) + len(seq2) - 2 * lcs_len(seq1, seq2)) / (len(seq1) + len(seq2))

    return dist


def lcs_min(seq1, seq2):
    """
    Computes the distance between two sequences using the formula below:

    D(X, Y) = 1 - LCS(|X|,|Y|) / min(|X|,|Y|),

    where LCS: the length of the Longest Common Subsequence between two sequences.

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    dist = 1 - (lcs_len(seq1, seq2) / min(len(seq1), len(seq2)))

    return dist


def lcs_ext(seq1, seq2):
    """
    Computes the distance between two sequences using the formula below:

    D(X, Y) = 1 - ( LCS(|X|,|Y|)^2 / (|X|*|Y|) ) * ( min(|X|,|Y|)^2 / max(|X|,|Y|)^2 ),

    where LCS: the length of the Longest Common Subsequence between the sequences.

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    l_seq1 = len(seq1)
    l_seq2 = len(seq2)
    lcss = lcs_len(seq1, seq2)
    min_l1l2 = min(l_seq1, l_seq2)
    max_l1l2 = max(l_seq1, l_seq2)
    dist = 1 - ((lcss ** 2) / (l_seq1 * l_seq2)) * ((min_l1l2 ** 2) / (max_l1l2 ** 2))

    return dist


def jaccard(seq1, seq2):
    """
    Computes the distance between two sequences using the formula below:

    D(X, Y) = 1 - |X intersection Y| / |X union Y|

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    dist = 1 - len(set(seq1).intersection(set(seq2))) / len(set(seq1).union(set(seq2)))
    return dist


def jaccard_min(seq1, seq2):
    """
    Computes the distance between two sequences using the formula below:

    D(X, Y) = 1 - |X intersection Y| / min(|X|,|Y|)

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    dist = 1 - len(set(seq1).intersection(set(seq2))) / min(len(set(seq1)), len(set(seq2)))
    return dist


def gestalt(seq1, seq2):
    """
    Computes the distance between two sequences using Python's difflib.SequenceMatcher:
    https://docs.python.org/2.7/library/difflib.html#difflib.SequenceMatcher

    This function is based on the algorithm proposed in:
    John W. Ratcliff and David Metzener, Pattern Matching: The Gestalt Approach, Dr. Dobb's Journal, page 46, July 1988.

    and is quite similar to the LCS algorithm.

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    sm = SequenceMatcher(None, seq1, seq2)
    dist = 1 - sm.ratio()
    return dist


def find_ngrams(seq, n):
    """
    Computes the ngrams for a sequence.

    :type seq: a list of of strings
    :param seq: a sequence
    :return a list where ngrams are stored
    """
    return zip(*[seq[i:] for i in range(n)])


def seqsim(seq1, seq2):
    """
    Computes the distance between two sequences using ngrams. This metric is defined in:

    Wang, Jue, et al. "Mining succinct and high-coverage API usage patterns from source code."
    Proceedings of the 10th Working Conference on Mining Software Repositories. IEEE Press, 2013.

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    ngrams1 = []
    ngrams2 = []
    for i in range(1, len(seq1) + 1):
        ngrams1.extend(find_ngrams(seq1, i))
    for i in range(1, len(seq2) + 1):
        ngrams2.extend(find_ngrams(seq2, i))

    intersection = set(ngrams1).intersection(set(ngrams2))
    union = set(ngrams1).union(set(ngrams2))

    sum_inter = sum(len(i) for i in intersection)
    sum_union = sum(len(i) for i in union)

    sim = sum_inter / sum_union
    dist = 1 - sim
    return dist


def levenshtein(seq1, seq2):
    """"
    This is a straightforward implementation of a well-known algorithm, and thus
    probably shouldn't be covered by copyright to begin with. But in case it is,
    the author (Magnus Lie Hetland) has, to the extent possible under law,
    dedicated all copyright and related and neighboring rights to this software
    to the public domain worldwide, by distributing it under the CC0 license,
    version 1.0. This software is distributed without any warranty. For more
    information, see <http://creativecommons.org/publicdomain/zero/1.0>

    :type seq1: a list of of strings
    :param seq1: a sequence
    :type seq2: a list of of strings
    :param seq2: a sequence
    :return dist: the distance
    """
    n, m = len(seq1), len(seq2)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        seq1,seq2 = seq2,seq1
        n,m = m,n

    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if seq1[j-1] != seq2[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)

    dist = current[n] / max(n, m)
    return dist


def is_subseq(seq1, seq2):
    it = iter(seq2)
    return all(any(c == ch for c in it) for ch in seq1)
