import sys,os
import re
import codecs
import csv
import xml.etree.ElementTree as ET
import shutil
import argparse
import inspect
import subprocess
import shlex
from bs4 import BeautifulSoup

import ArrayJob

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

    def extract_text_from_raw_collection(self):
        output_path = os.path.join(self.corpus_path, 'corpus')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for fn in os.listdir(self.raw_corpus_path):
            if os.path.exists( os.path.join(output_path, fn) ):
                continue
            with codecs.open( os.path.join(self.raw_corpus_path, fn), 'rb', 'utf-8' ) as f:
                bf = BeautifulSoup(f, 'lxml')
                with codecs.open( os.path.join(output_path, fn), 'wb', 'utf-8' ) as of:
                    for doc in bf.find_all('doc'):
                        of.write('<DOC>\n')
                        for ele in doc.contents:
                            if ele.name == 'docno' or ele.name == 'text':
                                of.write('%s\n' % (ele))
                        of.write('</DOC>\n')

    def build_index(self):
        # for microblog we build one index for each query!!!
        corpus_path = os.path.join(self.corpus_path, 'corpus')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for fn in os.listdir(corpus_path):
            if os.path.exists( os.path.join(self.index_root, fn) ):
                continue
            subprocess.call(['IndriBuildIndex_EX', '-index=%s'%os.path.join(index_root, fn), 
              'corpus=path:%s,class:%s' % (os.path.join(corpus_path, fn), 'trectext') ])


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
        MicroBlogIndex(args.regen_microblog_corpus[0]).extract_text_from_raw_collection()
    if args.build_microblog_index:
        MicroBlogIndex(args.build_microblog_index[0]).build_index()
