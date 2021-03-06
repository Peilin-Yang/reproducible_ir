# -*- coding: utf-8 -*-
import sys,os
import json
import csv
from operator import itemgetter
import numpy as np
import itertools
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse

reload(sys)
sys.setdefaultencoding('utf-8')


class Performances(object):
    """
    Handle the performace. For example, get all the performances of one method(has multiple parameters).
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.evaluation_results_root = os.path.join(self.corpus_path, 'evals')
        self.mb_decay_eval_results_root = os.path.join(self.corpus_path, 'evals_mb_decay')
        self.mb_combine_eval_results_root = os.path.join(self.corpus_path, 'evals_mb_combine')
        self.performances_root = os.path.join(self.corpus_path, 'performances')
        if not os.path.exists(self.performances_root):
            os.makedirs(self.performances_root)

    def gen_output_performances_paras(self):
        all_paras = []
        all_results = {}
        all_folders = [self.evaluation_results_root, self.mb_decay_eval_results_root, self.mb_combine_eval_results_root]
        for folder in all_folders:
            if os.path.exists( folder ):
                for fn in os.listdir(folder):
                    query_part = fn.split('-')[0]
                    method_paras = '-'.join(fn.split('-')[1:])
                    method_paras_split = method_paras.split(',')
                    method_name = method_paras_split[0].split(':')[1]
                    if 'perturb' in method_name:
                        method_paras_split = {ele.split(':')[0]:ele.split(':')[1] for ele in method_paras_split}
                        label = query_part+'-'+method_name+'_'+method_paras_split['perturb_type']
                    else:
                        label = query_part+'-'+method_name
                    compare_results_fn = os.path.join(self.performances_root, label)
                    if label not in all_results:
                        all_results[label] = []
                    all_results[label].append( os.path.join(folder, fn) )
                for label in all_results:
                    tmp = [ self.corpus_path, os.path.join(self.performances_root, label) ]
                    tmp.extend( all_results[label] )
                    all_paras.append(tuple(tmp))

        return all_paras

    def output_evaluation_results(self, methods=[], evaluation_method='map', query_part='title'):
        data = []
        all_folders = [self.evaluation_results_root, self.mb_decay_eval_results_root]
        for folder in all_folders:
            if os.path.exists( folder ):
                for fn in os.listdir(folder):
                    q_part = fn.split('-')[0]
                    if q_part != query_part:
                        continue
                    method_paras = '-'.join(fn.split('-')[1:])
                    method_paras_split = method_paras.split(',')
                    method_name = method_paras_split[0].split(':')[1]
                    if method_name not in methods:
                        continue
                    try:
                        para = method_paras_split[1].split(':')[1]
                    except:
                        continue
                    if 'perturb' in method_name:
                        method_paras_split = {ele.split(':')[0]:ele.split(':')[1] for ele in method_paras_split}
                        method_name += '_'+method_paras_split['perturb_type']
                        para = method_paras_split['perturb_var']
                    with open( os.path.join(folder, fn) ) as _in:
                        j = json.load(_in)
                        score = j['all'][evaluation_method]
                    data.append( (method_name+'_'+para, score) )
                    
        data.sort(key=itemgetter(0))
        header = ['function_name', evaluation_method]

        data.insert(0, header)
        with open( 'batch_eval_results_'+os.path.basename(self.corpus_path)+'.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(data)


    def output_performances(self, output_fn, eval_fn_list):
        all_results = {}
        for ele in eval_fn_list:
            paras = ','.join( '-'.join(os.path.basename(ele).split('-')[1:]).split(',')[1:] )
            with open(ele) as _in:
                j = json.load(_in)
                for eval_method in j['all']:
                    if eval_method not in all_results:
                        all_results[eval_method] = []
                    all_results[eval_method].append( (float(j['all'][eval_method]), paras) )
        final_results = {}
        for eval_method in all_results:
            all_results[eval_method].sort(key=itemgetter(0), reverse=True)
            num_a = np.array([ele[0] for ele in all_results[eval_method]])
            final_results[eval_method] = {'max': {'value':all_results[eval_method][0][0], 'para':all_results[eval_method][0][1]},
                'min': {'value':all_results[eval_method][-1][0], 'para':all_results[eval_method][-1][1]},
                'avg': np.mean(num_a), 'std': np.std(num_a)}

        with open(output_fn, 'wb') as o:
            json.dump(final_results, o, indent=2, sort_keys=True)


    def load_optimal_performance(self, evaluation_method='map', query_part='title'):
        data = []
        for fn in os.listdir(self.performances_root):
            q_part = fn.split('-')[0]
            if q_part != query_part:
                continue
            method_name = fn.split('-')[1]
            with open(os.path.join(self.performances_root, fn)) as pf:
                all_performance = json.load(pf)
                required = all_performance[evaluation_method]
                data.append( (method_name, required['max']['value'], required['max']['para']) )
        return data

    def print_optimal_performance(self, evaluation_method='map', query_part='title'):
        optimal_performances = self.load_optimal_performance(evaluation_method, query_part)
        optimal_performances.sort(key=itemgetter(0, 1, 2))
        for ele in optimal_performances:
            print ele[0], ele[1], ele[2]


if __name__ == '__main__':
    pass

