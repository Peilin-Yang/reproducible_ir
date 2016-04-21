# -*- coding: utf-8 -*-
import sys,os
import json
from inspect import currentframe, getframeinfo
import itertools
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
        self.pairwise_st_root = os.path.join(self.corpus_path, 'pairwise_significant_test')
        if not os.path.exists(self.st_root):
            os.makedirs(self.st_root)
        if not os.path.exists(self.pairwise_st_root):
            os.makedirs(self.pairwise_st_root)

    def sig_test_for_optimal(self, measure='map', use_which_part=['title']):
        other_collection = self.corpus_path+'_nostopwords'
        if not os.path.exists(other_collection):
            print other_collection+' does not exist!'
            exit(1)
        other_evaluation_root = os.path.join(other_collection, 'evals')
        other_perform_root = os.path.join(other_collection, 'performances')

        with open('g.json') as f:
            j = json.load(f)
            all_methods = [m['name'] for m in j['methods']]

        all_results = {}
        for fn in os.listdir(self.performance_root):
            #print fn
            query_part, method = fn.split('-')
            if query_part not in use_which_part or method not in all_methods:
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
                    this_all_perform = {qid:j[qid][measure] for qid in j if qid != 'all'}
                with open(other_eval_fn) as f:
                    j = json.load(f)
                    other_all_perform = {qid:j[qid][measure] for qid in j if qid != 'all'}
                #print method, this_opt_para, other_opt_para
                this_all_perform_list = [this_all_perform[k] for k in this_all_perform if k in other_all_perform]
                other_all_perform_list = [other_all_perform[k] for k in this_all_perform if k in other_all_perform]
                if query_part not in all_results:
                    all_results[query_part] = {}
                all_results[query_part][method] = [this_opt_perform, other_opt_perform, 
                    stats.ttest_rel(this_all_perform_list, other_all_perform_list)]
        for query_part in all_results:
            with open(os.path.join(self.st_root, query_part), 'wb') as f:
                for method in all_results[query_part]:
                    f.write('%s,%.3f,%.3f,%.3f,%.3f\n' % 
                        (method, all_results[query_part][method][0],
                            all_results[query_part][method][1],
                            all_results[query_part][method][2][0],
                            all_results[query_part][method][2][1]/2.0))

    def pairwise_sig_test(self, measure='map', use_which_part=['title'], cal_type=2):
        """
        Compare each pair of ranking models for each collection.
        See whether one model outperforms the other model.
        cal_type: 
        0-one tailed paired t-test; 1-two tailed paired t-test; 2-two tailed paired wilcoxon
        """
        if 'clueweb' in self.corpus_path:
            measure = 'err_cut_20'

        with open('g.json') as f:
            j = json.load(f)
            all_methods = [m['name'] for m in j['methods']]
            methods_mapping = {m['name']:m['formal_name'] for m in j['methods']}

        all_results = {}
        for fn in os.listdir(self.performance_root):
            query_part, method = fn.split('-')
            if query_part not in use_which_part or method not in all_methods:
                continue
            with open(os.path.join(self.performance_root, fn)) as pf1:
                j = json.load(pf1)
                this_opt_perform = j[measure]['max']['value']
                this_opt_para = j[measure]['max']['para']
            #print query_part, method, this_opt_perform, other_opt_perform
            this_eval_fn = os.path.join(self.evaluation_root, query_part+'-method:'+method)
            if this_opt_para:
                this_eval_fn += ','+this_opt_para
            with open(this_eval_fn) as f:
                j = json.load(f)
                this_all_perform = {qid:j[qid][measure] for qid in j if qid != 'all'}
            #print method, this_opt_para, other_opt_para
            if query_part not in all_results:
                all_results[query_part] = {}
            all_results[query_part][method] = this_all_perform
        
        final_results = {}
        for query_part in all_results:
            for ele in itertools.permutations(all_methods, 2):
                m1_list = [all_results[query_part][ele[0]][k] for k in all_results[query_part][ele[0]] if k in all_results[query_part][ele[1]]]
                m2_list = [all_results[query_part][ele[1]][k] for k in all_results[query_part][ele[1]] if k in all_results[query_part][ele[0]]]
                if cal_type == 2:
                    try:
                        t, p = stats.wilcoxon(m1_list, m2_list)
                        print methods_mapping[ele[0]], methods_mapping[ele[1]]
                        print t, p
                        raw_input()
                    except: # which means that the two lists are exactly the same
                        continue
                else:
                    t, p = stats.ttest_rel(m1_list, m2_list)
                m1 = methods_mapping[ele[0]]
                m2 = methods_mapping[ele[1]]
                if cal_type == 0:
                    critieria = p/2.0
                elif cal_type == 1 or cal_type == 2:
                    critieria = p
                if critieria < 0.05:
                    if t > 0:
                        if m1 not in final_results:
                            final_results[m1] = set()
                        final_results[m1].add(m2)
                    else:
                        if m2 not in final_results:
                            final_results[m2] = set()
                        final_results[m2].add(m1)
        for m in final_results:
            final_results[m] = list(final_results[m])
        with open(os.path.join(self.pairwise_st_root, query_part+'-'+str(cal_type)), 'wb') as f:
            json.dump(final_results, f, indent=2, sort_keys=True)


if __name__ == '__main__':
    pass

