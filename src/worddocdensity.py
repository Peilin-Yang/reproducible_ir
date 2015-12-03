# -*- coding: utf-8 -*-
import sys,os
import codecs
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse

from query import Query

reload(sys)
sys.setdefaultencoding('utf-8')


class WordDocDensity(object):
    """
    Output the WordDocDensity for queries.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.index_fn = os.path.join(self.corpus_path, 'index')
        self.dd_fn = os.path.join(self.corpus_path, 'all_queries_terms')
        self.dd_root = os.path.join(self.corpus_path, 'queries_dd')
        if not os.path.exists(self.dd_root):
            os.makedirs(self.dd_root)

    def gen_output_dd_paras(self, use_which_part=['title']):
        term_set = set()
        queries = Query(self.corpus_path).get_queries()
        for ele in queries:
            for part in use_which_part:
                for sep_part in part.split('+'):
                    for term in ele[sep_part].split():
                        term_set.add( term.strip() )
        with codecs.open(self.dd_fn, 'wb', 'utf-8') as f:
            f.write('\n'.join(list(term_set)))
        all_paras = [(self.corpus_path, self.dd_fn, self.dd_root)]
        return all_paras

    def output_dd(self):
        raw_p = 'IndriWordDocDensity -index=%s -file=%s' % ( self.index_fn, self.dd_fn )

        p = Popen(raw_p.split(), stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        for line in stdout.split('\n'):
            line = line.strip()
            if line:
                row = line.split()
                stemmed_term = row[1]
                with open( os.path.join(self.dd_root, stemmed_term), 'wb' ) as f:
                    f.write(row[2])

if __name__ == '__main__':
    pass

