import os
import gc
import subprocess

from apisummariser.helper import filefunctions


def beautify_examples(beautifier_path, res_dir):
    """
    Applies the Artistic Style formatter to the generated snippets.

    :type beautifier_path: string
    :param beautifier_path: the filepath of the astyle formatter's executable
    :type res_dir: the current session's results directory
    :param res_dir:
    :return:
    """
    examples_paths = os.path.join(res_dir, 'medoids', '*.java')
    gc.collect()
    p = subprocess.Popen([beautifier_path, '--style=java', '--delete-empty-lines','--recursive', examples_paths],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.communicate()[0]

    orig_paths = os.path.join(res_dir, 'medoids')
    # remove the original files
    filefunctions.delete_files_recurs(orig_paths, '.orig')
