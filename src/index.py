import sys,os
import codecs
import json
import argparse
import inspect
from inspect import currentframe, getframeinfo
import subprocess
import shlex

reload(sys)
sys.setdefaultencoding('utf-8')


class Index(object):
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

class MicroBlogIndex(Index):
    def __init__(self, collection_path):
        super(MicroBlogIndex, self).__init__(collection_path)
        self.raw_corpus_path = os.path.join( self.corpus_path, 'raw_corpus')
        if not os.path.exists( self.raw_corpus_path ):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Index Constructor]:No raw corpus path...exit...'
            exit(1)        
        self.index_root = os.path.join(self.corpus_path, 'index') # for microblog collection, we need to build one index for each query
        if not os.path.exists(self.index_root):
            os.makedirs( self.index_root )
        self.build_index_para_root = os.path.join(self.corpus_path, 'build_index_paras') # for microblog collection, we need to build one index for each query
        if not os.path.exists(self.build_index_para_root):
            os.makedirs( self.build_index_para_root )

    def transform_raw_corpus(self):
        output_path = os.path.join(self.corpus_path, 'corpus')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for fn in os.listdir(self.raw_corpus_path):
            if os.path.exists( os.path.join(output_path, fn) ):
                continue
            with codecs.open( os.path.join(self.raw_corpus_path, fn), 'rb', 'utf-8' ) as f:
                j = json.load(f)
                with codecs.open( os.path.join(output_path, fn), 'wb', 'utf-8' ) as of:
                    for doc in j:
                        of.write('<DOC>\n')
                        of.write('<DOCNO>%s</DOCNO>\n' % (doc['id']))
                        of.write('<TEXT>%s</TEXT>\n' % (doc['text']))
                        of.write('</DOC>\n')

    def gen_build_index_para_file(self, para_file_path, gen_index_path, corpus_path, _class='trectext'):
        with open(para_file_path, 'wb') as f:
            f.write('<parameters>\n')
            f.write('\t<memory>1g</memory>\n')
            f.write('\t<index>%s</index>\n' % gen_index_path)
            f.write('\t<corpus>\n')
            f.write('\t\t<path>%s</path>\n' % corpus_path)
            f.write('\t\t<class>%s</class>\n' % _class)
            f.write('\t</corpus>\n')
            f.write('\t<stemmer>\n')
            f.write('\t\t<name>porter</name>\n')
            f.write('\t</stemmer>\n')
            f.write('</parameters>\n')

    def build_index(self):
        # for microblog we build one index for each query!!!
        corpus_path = os.path.join(self.corpus_path, 'corpus')
        for fn in os.listdir(corpus_path):
            if not os.path.exists( os.path.join(self.build_index_para_root, fn) ):
                self.gen_build_index_para_file(
                  os.path.join(self.build_index_para_root, fn),
                  os.path.join(self.index_root, fn), 
                  os.path.join(corpus_path, fn))
            if not os.path.exists( os.path.join(self.index_root, fn) ):
                subprocess.call(['IndriBuildIndex_EX', os.path.join(self.build_index_para_root, fn)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--regen_microblog_corpus",
        nargs=1,
        help="Re-generate MicroBlog Corpus")

    parser.add_argument("-i", "--build_microblog_index",
        nargs=1,
        help="Build Index")

    args = parser.parse_args()

    if args.regen_microblog_corpus:
        MicroBlogIndex(args.regen_microblog_corpus[0]).transform_raw_corpus()
    if args.build_microblog_index:
        MicroBlogIndex(args.build_microblog_index[0]).build_index()
