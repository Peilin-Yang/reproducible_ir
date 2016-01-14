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
        for fn in os.listdir(self.raw_corpus_path):
            with open( os.path.join(self.raw_corpus_path, fn) ) as f:
                bf = BeautifulSoup(f, 'lxml')
                print bf

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--regen_microblog_corpus",
        nargs=1,
        help="Re-generate MicroBlog Corpus")

    args = parser.parse_args()

    if args.regen_microblog_corpus:
        MicroBlogIndex(args.regen_microblog_corpus[0]).extract_text_from_raw_collection()

