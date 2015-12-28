# -*- coding: utf-8 -*-
import sys,os
import json
from inspect import currentframe, getframeinfo
import argparse

from scipy import stats

reload(sys)
sys.setdefaultencoding('utf-8')


class SignificantTest(object):
    """
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.evaluation_root = os.path.join(self.corpus_path, 'evals')
        self.performance_root = os.path.join(self.corpus_path, 'performances')
        self.st_root = os.path.join(self.corpus_path, 'significant_test')
        if not os.path.exists(self.st_root):
            os.makedirs(self.st_root)

    def sig_test_for_optimal(self, measure='map', use_which_part=['title']):
        other_collection = self.corpus_path+'_nostopwords'
        if not os.path.exists(other_collection):
            print other_collection+' does not exist!'
            exit(1)
        other_evaluation_root = os.path.join(other_collection, 'evals')
        other_perform_root = os.path.join(other_collection, 'performances')

        all_paras = []
        all_results = {}
        for fn in os.listdir(self.performance_root):
            #print fn
            query_part, method = fn.split('-')
            if query_part not in use_which_part:
                continue
            if os.path.exists(os.path.join(other_perform_root, fn)):
                with open(os.path.join(self.performance_root, fn)) as pf1:
                    j = json.load(pf1)
                    this_opt_perform = j[measure]['max']['value']
                    this_opt_para = j[measure]['max']['para']
                with open(os.path.join(other_perform_root, fn)) as pf1:
                    j = json.load(pf1)
                    other_opt_perform = j[measure]['max']['value']
                    other_opt_para = j[measure]['max']['para']  
                #print query_part, method, this_opt_perform, other_opt_perform
                this_eval_fn = os.path.join(self.evaluation_root, query_part+'-method:'+method)
                other_eval_fn = os.path.join(other_evaluation_root, query_part+'-method:'+method)
                if this_opt_para:
                    this_eval_fn += ','+this_opt_para
                if other_opt_para:
                    other_eval_fn += ','+other_opt_para
                with open(this_eval_fn) as f:
                    j = json.load(f)
                    this_all_perform = {qid:j[qid][measure] for qid in j[qid] if qid != 'all'}
                with open(other_eval_fn) as f:
                    j = json.load(f)
                    other_all_perform = {qid:j[qid][measure] for qid in j[qid] if qid != 'all'}
                print this_all_perform
                print other_all_perform
                exit()


if __name__ == '__main__':
    pass

