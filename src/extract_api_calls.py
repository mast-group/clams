from subprocess import Popen, PIPE


class APICallExtractor:
    def __init__(self, extractor_path):
        """
        :type extractor_path: str
        :param extractor_path: the tool's path
        """
        self.extractor_path = extractor_path

    def extract(self, params):
        """
        {'libDir', 'libName', 'packageName', 'outDir', 'resolveWildcards', 'exampleDir', 'namespaceDir', 'srcDirs'}
        :param params:
        :return:
        """
        args = ['java', '-jar', self.extractor_path, '-ld', params['lib-dir'], '-ln', params['lib-name'],
                '-pn', params['package-name'], '-of', params['out-file']]
        if params['resolve-wildcards']:
            args.extend(
                ['-rw', '-ed', params['example-dir'], '-nd', params['namespace-dir']])
        p = Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE)

        for line in p.stdout:
            print line,
