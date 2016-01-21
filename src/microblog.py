# -*- coding: utf-8 -*-
import sys,os
import json
import re
import csv
import ast
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from dateutil.relativedelta import *
import itertools
from operator import itemgetter
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse
import math
import numpy as np

import performance

reload(sys)
sys.setdefaultencoding('utf-8')


def exponential(x, _lambda=0.1):
    return np.exp((-1)*x*_lambda)

def log_normal(diff, _mu=1.0, _lambda=1):
    x = np.divide(np.add(np.log(diff), -_mu), _lambda)
    _sum = np.copy(x)
    _values = np.copy(x)
    for i in range(1, 100):
        _values = _values*x*x/(2*i+1)
        _sum += _values
    phi = 0.5+(_sum/math.sqrt(2*math.pi))*np.exp(x*x/(-2.0))
    return 1 - phi

def log_logistic(diff, _mu=1.0, _lambda=1):
    A = np.exp(_mu/_lambda)
    return A/(A+np.power(diff, 1.0/_lambda))

def linear_cal(x):
    if x <=0:
        return 0
    return x

def linear(diff, _slope=-1.0, _intercept=0.5):
    A = diff*_slope+_intercept
    vfunc = np.vectorize(linear_cal)
    return vfunc(A)

class MicroBlog(object):
    """
    MicroBlog Related
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.query_file_path = os.path.join(self.corpus_path, 'raw_topics')
        if not os.path.exists(self.query_file_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print """No query file found! 
                query file should be called "raw_topics" under 
                corpus path. You can create a symlink for it"""
            exit(1)

        self.parsed_query_file_path = os.path.join(self.corpus_path, 'parsed_topics.json')
        self.raw_corpus_root = os.path.join(self.corpus_path, 'raw_corpus')
        self.decay_results_root = os.path.join(self.corpus_path, 'decay_results')
        self.merged_rel_results_root = os.path.join(self.corpus_path, 'merged_results')
        self.merged_decay_results_root = os.path.join(self.corpus_path, 'merged_decay_results')
        if not os.path.exists(self.merged_decay_results_root):
            os.makedirs(self.merged_decay_results_root)
        self.combine_results_root = os.path.join(self.corpus_path, 'combined_results')
        self.merged_combine_results_root = os.path.join(self.corpus_path, 'merged_combined_results')
        if not os.path.exists(self.merged_combine_results_root):
            os.makedirs(self.merged_combine_results_root)
        self.eval_rel_root = os.path.join(self.corpus_path, 'evals')
        self.eval_decay_root = os.path.join(self.corpus_path, 'evals_mb_decay')
        if not os.path.exists(self.eval_decay_root):
            os.makedirs(self.eval_decay_root)
        self.eval_combine_root = os.path.join(self.corpus_path, 'evals_mb_combine')
        if not os.path.exists(self.eval_combine_root):
            os.makedirs(self.eval_combine_root)
        self.qrel_path = os.path.join(self.corpus_path, 'judgement_file')

    def gen_run_split_decay_paras(self, methods, query_part='title'):
        all_paras = []
        if not os.path.exists(self.decay_results_root):
            os.makedirs(self.decay_results_root)
        with open( self.parsed_query_file_path ) as f:
            j = json.load(f)
            for ele in j:
                raw_qid = ele['num']
                qid = str(int(ele['num'][2:]))
                for m in methods:
                    if 'paras' in m:
                        for p in itertools.product(*[ele[1] for ele in m['paras'].items()]):
                            para_str = m['name']
                            tmp = '-method:%s4h' % m['name']
                            for k_idx, k in enumerate(m['paras'].keys()):
                                para_str += ',%s:%s' % (k, p[k_idx])
                                tmp += ',%s:%s' % (k, p[k_idx])
                            results_fn = os.path.join(self.decay_results_root, query_part+'_'+qid+tmp)
                            if not os.path.exists(results_fn):
                                all_paras.append( (self.corpus_path, raw_qid, para_str, results_fn) )
                    else:
                        para_str = m['name']
                        results_fn = os.path.join(self.decay_results_root, query_part+'_'+'-method:%s4h' % m['name'])
                        if not os.path.exists(results_fn):
                            all_paras.append( (self.corpus_path, raw_qid, para_str, results_fn) )
        return all_paras

    def cal_diffs(self, qid, corpus_path):
        query_time = ''
        diffs = []
        docid_set = set()
        with open(self.parsed_query_file_path) as f:
            j = json.load(f)
            for ele in j:
                if ele['num'] == qid:
                    # try:
                    #     querytime = datetime.strptime(ele['querytime'], '%a %b %d %H:%M:%S %z %Y')
                    # except:
                    #     querytime = datetime.strptime(ele['querytime'], '%a %b %d %H:%M:%S %Z %Y')
                    querytime = parser.parse(ele['querytime'])
                    #print querytime
                    break
        with open(corpus_path) as f:
            j = json.load(f)
            for doc in j:
                docid = doc['id']
                if docid in docid_set:
                    continue
                docid_set.add(docid)
                doctime = datetime.fromtimestamp(float(doc['epoch']), pytz.utc)
                diff = ((querytime-doctime).total_seconds())/3600.0/4.0 # 4h interval
                diffs.append([docid, diff])
        return diffs

    def output_results(self, output_fn, qid, scores, runid):
        with open(output_fn, 'wb') as f:
            idx = 1
            for ele in scores:
                docid = ele[0]
                score = ele[1]
                f.write('%d Q0 %s %d %f %s\n' % (int(qid[2:]), docid, idx, score, runid))
                idx += 1

    def cal_the_decay_results(self, qid, method_n_para, output_fn):
        #print self.raw_corpus_root, qid
        corpus_path = os.path.join(self.raw_corpus_root, qid)
        diffs = self.cal_diffs(qid, corpus_path)
        #print diffs
        diffs_array = np.asarray([ele[1] for ele in diffs])
        method = method_n_para.split(',')[0]
        if len(method_n_para.split(',')) > 1:
            paras = {ele.split(':')[0]:float(ele.split(':')[1]) for ele in method_n_para.split(',')[1:]}
        #print method, paras
        if 'linear' in method:
            scores = linear(diffs_array, paras['slope'], paras['intercept'])
        if 'exponential' in method:
            scores = exponential(diffs_array, paras['lambda'])
        if 'lognormal' in method:
            scores = log_normal(diffs_array, paras['mu'], paras['sigma'])
        if 'loglogistic' in method:
            scores = log_logistic(diffs_array, paras['mu'], paras['sigma'])
        #print scores
        res = [(diffs[i][0], scores[i]) for i in range(len(diffs))]
        res.sort(key=itemgetter(1), reverse=True)
        self.output_results(output_fn, qid, res, method_n_para)


    def gen_output_combined_rel_decay_scores_para(self):
        all_paras = []
        rel_funcs = ['okapi','pivoted','f2exp']
        all_methods = []
        p = performance.Performances(self.corpus_path)
        scores = {}
        output_folder = os.path.join(self.corpus_path, 'optimal_scores_norm')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if '2011' in self.corpus_path or '2012' in self.corpus_path:
            query_part = 'title'
        else:
            query_part = 'query'
        optimal_pfms = p.load_optimal_performance('map', query_part)

        paths = {ele[0]:os.path.join(self.merged_rel_results_root, query_part+'-method:'+ele[0]+','+ele[2]) for ele in optimal_pfms if ele[0] in rel_funcs}
        for fn in os.listdir(self.merged_decay_results_root):
            recency_func = ':'.join(fn.split(':')[1:])
            paths[recency_func] = os.path.join(self.merged_decay_results_root, fn)
        #print paths
        for method, path in paths.items():
            all_methods.append(method)
            if os.path.exists(os.path.join(output_folder, method)):
                continue
            scores[method] = {}
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        row = line.split()
                        qid = row[0]
                        did = row[2]
                        try:
                            score = float(row[4])
                        except:
                            score = 0.0
                        if qid not in scores[method]:
                            scores[method][qid] = {}
                        scores[method][qid][did] = score

        for method in scores:
            if os.path.exists(os.path.join(output_folder, method)):
                continue 
            #print method
            with open(os.path.join(output_folder, method), 'wb') as f:
                for qid in scores[method]:
                    this_scores = scores[method][qid].values()
                    min_s = min(this_scores)
                    max_s = max(this_scores)
                    if max_s-min_s != 0:
                        #print min_s, max_s
                        for did in scores[method][qid]: 
                            scores[method][qid][did] = (scores[method][qid][did]-min_s)/(max_s-min_s)
                            f.write('%s,%s,%f\n' % (qid, did, scores[method][qid][did]))

        for rel_func in rel_funcs:            
            for method in all_methods:
                if method in rel_funcs:
                    continue
                recency_func = method
                name = rel_func+'_'+recency_func
                for a in np.arange(0.1, 1.0, 0.1):
                    output_path = os.path.join(self.merged_combine_results_root, query_part+'-method:'+name+',a:%.1f'%a)
                    if not os.path.exists(output_path):
                        all_paras.append( (self.corpus_path, query_part, rel_func, recency_func, a) )
        return all_paras


    def output_combined_rel_decay_scores(self, query_part, rel_func, recency_func, a):
        output_folder = os.path.join(self.corpus_path, 'optimal_scores_norm')
        scores = {}
        for method in [rel_func, recency_func]:
            with open( os.path.join(output_folder, method) ) as f:
                r = csv.reader(f)
                scores[method] = {}
                for row in r:
                    qid = row[0]
                    docid = row[1]
                    score = float(row[2])
                    if qid not in scores[method]:
                        scores[method][qid] = {}
                    scores[method][qid][docid] = score

        name = rel_func+'_'+recency_func
        output_path = os.path.join(self.merged_combine_results_root, query_part+'-method:'+name+',a:%.1f'%a)
        with open(output_path, 'wb') as f:
            for qid in scores[recency_func]:
                for docid in scores[recency_func][qid]:
                    #print scores[recency_func][qid][docid]
                    score = a*scores[recency_func][qid][docid]
                    if qid in scores[rel_func] and docid in scores[rel_func][qid]:
                        score += (1-a)*scores[rel_func][qid][docid]
                    f.write('%s Q0 %s 0 %f %s\n' % (qid, docid, score, name))

    def gen_merge_decay_results_paras(self, total_query_cnt, use_which_part=['title']):
        all_paras = []
        all_results = {}
        for fn in os.listdir(self.decay_results_root):
            #print fn
            query = fn.split('-')[0]
            method = '-'.join(fn.split('-')[1:])
            query_part, qid = query.split('_')
            label = query_part+'-'+method
            collect_results_fn = os.path.join(self.merged_decay_results_root, label)
            if not os.path.exists(collect_results_fn):
                if label not in all_results:
                    all_results[label] = []
                all_results[label].append( os.path.join(self.decay_results_root, fn) )

        for label in all_results:
            if len(all_results[label]) < total_query_cnt:
                print 'Results of '+ self.corpus_path + ':' + label +' not enough (%d/%d).' % (len(all_results[label]), total_query_cnt)
                continue
            tmp = [os.path.join(self.merged_decay_results_root, label)]
            tmp.extend( all_results[label] )
            all_paras.append(tmp)

        return all_paras

    def gen_eval_results_paras(self, qrel_program_str):
        all_paras = []
        folders = [self.merged_decay_results_root, self.merged_combine_results_root]
        for folder in folders:
            if os.path.exists(folder):
                eval_root = self.eval_decay_root if folder == self.merged_decay_results_root else self.eval_combine_root
                for fn in os.listdir(folder):
                    if not os.path.exists( os.path.join(eval_root, fn) ):
                        all_paras.append( (self.corpus_path, qrel_program_str, os.path.join(folder, fn), os.path.join(eval_root, fn)) )
        return all_paras


    def combined_funcs_significant_test(self, eval_method='map'):
        rel_funcs = ['okapi','pivoted','f2exp']
        if '2011' in self.corpus_path or '2012' in self.corpus_path:
            query_part = 'title'
        else:
            query_part = 'query'
        optimal_pfms = p.load_optimal_performance('map', query_part)
        methods_sets = {}
        for p in optimal_pfms:
            method = p[0]
            optimal_para = p[1]
            score = p[2]
            if method in rel_funcs:
                if method not in methods_sets:
                    methods_sets[method] = {}
                with open( os.path.join(self.eval_rel_root, method) ) as f:
                    j = json.load(f)
                    methods_sets[method]['base'] = {k:j[k][eval_method] for k in j if k != 'all'}
        print methods_sets


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-mb_decay", "--cal_the_decay_results",
        nargs=1,
        help="input: function_name and paras")

    parser.add_argument("-sig_test", "--significant_test",
        nargs=1,
        help="input: collection_path and evaluation method")

    args = parser.parse_args()

    if args.cal_the_decay_results:
        MicroBlog(args.cal_the_decay_results[0]).cal_the_decay_results()

    if args.significant_test:
        MicroBlog(args.significant_test[0]).combined_funcs_significant_test(args.significant_test[1])
        