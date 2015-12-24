import os,sys
import codecs
import subprocess
from subprocess import Popen, PIPE
import shlex
import re
import shutil
import argparse
import json
import csv
from operator import itemgetter
import multiprocessing
import inspect

import ArrayJob
import query
from worddocdensity import WordDocDensity
from smart import SMART
from results import Results
import g
import evaluation
import performance
from highchart import Highchart

_root = '../collections/'

def gen_batch_framework(para_label, batch_pythonscript_para, all_paras, \
        quote_command=False, memory='2G', max_task_per_node=50000, num_task_per_node=100):

    para_dir = os.path.join('batch_paras', '%s') % para_label
    if os.path.exists(para_dir):
        shutil.rmtree(para_dir)
    os.makedirs(para_dir)

    batch_script_root = 'bin'
    if not os.path.exists(batch_script_root):
        os.makedirs(batch_script_root)

    if len(all_paras) == 0:
        print 'Nothing to run for ' + para_label
        return

    tasks_cnt_per_node = min(num_task_per_node, max_task_per_node) if len(all_paras) > num_task_per_node else 1
    all_paras = [all_paras[t: t+tasks_cnt_per_node] for t in range(0, len(all_paras), tasks_cnt_per_node)]
    batch_script_fn = os.path.join(batch_script_root, '%s-0.qs' % (para_label) )
    batch_para_fn = os.path.join(para_dir, 'para_file_0')
    with open(batch_para_fn, 'wb') as bf:
        for i, ele in enumerate(all_paras):
            para_file_fn = os.path.join(para_dir, 'para_file_%d' % (i+1))
            bf.write('%s\n' % (para_file_fn))
            with open(para_file_fn, 'wb') as f:
                writer = csv.writer(f)
                writer.writerows(ele)
    command = 'python %s -%s' % (
        inspect.getfile(inspect.currentframe()), \
        batch_pythonscript_para
    )
    arrayjob_script = ArrayJob.ArrayJob()
    arrayjob_script.output_batch_qs_file(batch_script_fn, command, quote_command, True, batch_para_fn, len(all_paras), _memory=memory)
    run_batch_gen_query_command = 'qsub %s' % batch_script_fn
    subprocess.call( shlex.split(run_batch_gen_query_command) )
    """
    for i, ele in enumerate(all_paras):
        batch_script_fn = os.path.join( batch_script_root, '%s-%d.qs' % (para_label, i) )
        batch_para_fn = os.path.join(para_dir, 'para_file_%d' % i)
        with open(batch_para_fn, 'wb') as bf:
            bf.write('\n'.join(ele))
        command = 'python %s -%s' % (
            inspect.getfile(inspect.currentframe()), \
            batch_pythonscript_para
        )
        arrayjob_script = ArrayJob.ArrayJob()
        arrayjob_script.output_batch_qs_file(batch_script_fn, command, quote_command, True, batch_para_fn, len(ele))
        run_batch_gen_query_command = 'qsub %s' % batch_script_fn
        subprocess.call( shlex.split(run_batch_gen_query_command) )
    """


def gen_split_queries(remove_stopwords=False):
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        q['query_class'](collection_path).gen_query_file_for_indri( 
            remove_stopwords=remove_stopwords, use_which_part=q['qf_parts']
        )   


def gen_run_query_batch():
    all_paras = []
    with open('g.json') as f:
        methods = json.load(f)['methods']
        for q in g.query:
            collection_name = q['collection']
            collection_path = os.path.join(_root, collection_name)
            all_paras.extend(q['query_class'](collection_path).gen_run_split_query_paras( 
                methods,
                use_which_part=q['qf_parts']
            ) )

    #print all_paras
    gen_batch_framework('run_split_queries', 'b2', all_paras)


def run_query_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            query_fn = row[0]
            query_para = row[1]
            output_fn = row[2]
            run_query(query_fn, query_para, output_fn)
            
def run_query(query_fn, query_para, output_fn):
    p = Popen(['IndriRunQuery_EX', query_fn, query_para], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if 'EXCEPT' not in stdout:
        with open(output_fn, 'wb') as o:
            o.write(stdout)
    else:
        print line, stdout


def gen_merge_split_results_batch():
    all_paras = []
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        all_paras.extend( Results(collection_path).gen_merge_split_results_paras(q['cnt'], use_which_part=q['qf_parts']) )

    #print all_paras
    gen_batch_framework('merge_results', 'c2', all_paras)


def merge_split_results_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            output_fn = row[0]
            input_fns = row[1:]
            with open(output_fn, 'wb') as o:
                for ele in input_fns:
                    with open(ele) as _in:
                        o.write(_in.read())

def gen_eval_batch():
    all_paras = []
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        all_paras.extend( evaluation.Evaluation(collection_path).gen_eval_results_paras(q['qrel_program']) )

    #print all_paras
    gen_batch_framework('eval_results', 'd2', all_paras)

def eval_atom(fn):
    #print fn
    with open(fn) as f:
        reader = csv.reader(f)
        for row in reader:
            collection_path = row[0]
            qrel_program = row[1].split()
            results_fn = row[2]
            eval_results_fn = row[3]
            collection_name = collection_path.split('/')[-1]
            for q in g.query:
                if q['collection'] == collection_name:
                    q['query_class'](collection_path).output_all_evaluations(qrel_program, results_fn, eval_results_fn)
                    break
                    

def gen_output_performances_batch(eval_method='map'):
    all_paras = []
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        all_paras.extend( performance.Performances(collection_path).gen_output_performances_paras() )

    #print all_paras
    gen_batch_framework('gen_performances', 'e2', all_paras)


def output_performances_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            collection_path = row[0]
            output_fn = row[1]
            input_fns = row[2:]
            performance.Performances(collection_path).output_performances(output_fn, input_fns)


def gen_output_highcharts_batch():
    all_paras = []
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        all_paras.extend( Highchart(collection_path).gen_output_highcharts_paras() )
    gen_batch_framework('gen_highcharts', 'f2', all_paras)

def output_highcharts_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            collection_path = row[0]
            output_folder = row[1]
            input_fns = row[2:]
            Highchart(collection_path).output_highcharts(output_folder, input_fns)


def gen_output_worddocdensity_batch():
    all_paras = []
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        all_paras.extend( WordDocDensity(collection_path).gen_output_dd_paras(use_which_part=q['qf_parts']) )

    #print all_paras
    gen_batch_framework('gen_worddocdensity', 'w2', all_paras)

def output_worddocdensity_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            collection_path = row[0]
            WordDocDensity(collection_path).output_dd()


def gen_output_smart_ctf_batch():
    all_paras = []
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        all_paras.extend( SMART(collection_path).gen_output_ctf_paras(use_which_part=q['qf_parts']) )

    #print all_paras
    gen_batch_framework('gen_smart_ctf', 's2', all_paras)

def output_smart_ctf_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            collection_path = row[0]
            SMART(collection_path).output_ctf()


def del_method_related_files(method_name):
    folders = ['split_results', 'merged_results', 'evals', 'performances']
    for q in g.query:
        collection_name = q['collection']
        collection_path = os.path.join(_root, collection_name)
        for f in folders:
            if os.path.exists( os.path.join(collection_path, f) ):
                print 'Deleting ' + os.path.join(collection_path, f) + ' *' + method_name + '*'
                if f == 'split_results' or f == 'merged_results':
                    subprocess.call('find %s -name "*method:%s*" -exec rm -rf {} \\;' % (os.path.join(collection_path, f), method_name), shell=True)
                else:
                    subprocess.call('find %s -name "*%s*" -exec rm -rf {} \\;' % (os.path.join(collection_path, f), method_name), shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--gen_split_queries",
        nargs=1,
        help="First Step: Generate the split queries (one query file only contains one qid)")

    parser.add_argument("-b1", "--gen_run_query_batch",
        action='store_true',
        help="Second Step: Generate the batch run query para files")
    parser.add_argument("-b2", "--run_query_atom",
        nargs=1,
        help="Second Step: Run Query")

    parser.add_argument("-c1", "--gen_merge_split_results_batch",
        action='store_true',
        help="Third Step: We split the results by qid and by method(with paras). Now it is time to merge them.")
    parser.add_argument("-c2", "--merge_split_results_atom",
        nargs=1,
        help="Third Step: Do merge the results.")

    parser.add_argument("-d1", "--gen_eval_batch",
        action='store_true',
        help="Fourth Step: Evaluate the results")
    parser.add_argument("-d2", "--eval_atom",
        nargs=1,
        help="Fourth Step: Evaluate the results")

    parser.add_argument("-e1", "--gen_output_performances_batch",
        action='store_true',
        help="Fifth Step: Generate the performance of each method (for all possible parameters), e.g. best, worst, mean, std")
    parser.add_argument("-e2", "--output_performances_atom",
        nargs=1,
        help="Fifth Step: Generate the performance of each method (for all possible parameters), e.g. best, worst, mean, std")

    parser.add_argument("-f1", "--gen_output_highcharts_batch",
        action='store_true',
        help="Generate the highcharts of the best results.")   
    parser.add_argument("-f2", "--output_highcharts_atom",
        nargs=1,
        help="Generate the highcharts of the best results.")   

    parser.add_argument("-w1", "--gen_output_worddocdensity_batch",
        action='store_true',
        help="Generate the dd for worddocdensity method")   
    parser.add_argument("-w2", "--output_worddocdensity_atom",
        nargs=1,
        help="Generate the dd for worddocdensity method.")   

    parser.add_argument("-s1", "--gen_output_smart_ctf_batch",
        action='store_true',
        help="Generate the collection term weight for smart method")   
    parser.add_argument("-s2", "--output_smart_ctf_atom",
        nargs=1,
        help="Generate the collection term weight for smart method.") 

    parser.add_argument("-del", "--del_method_related_files",
        nargs=1,
        help="Delete all the output files of a method.")

    args = parser.parse_args()

    if args.gen_split_queries:
        use_stopwords = False if args.gen_split_queries[0] == '0' else True
        gen_split_queries(use_stopwords)

    if args.gen_run_query_batch:
        gen_run_query_batch()
    if args.run_query_atom:
        run_query_atom(args.run_query_atom[0])

    if args.gen_merge_split_results_batch:
        gen_merge_split_results_batch()
    if args.merge_split_results_atom:
        merge_split_results_atom(args.merge_split_results_atom[0])

    if args.gen_eval_batch:
        gen_eval_batch()
    if args.eval_atom:
        eval_atom(args.eval_atom[0])

    if args.gen_output_performances_batch:
        gen_output_performances_batch()
    if args.output_performances_atom:
        output_performances_atom(args.output_performances_atom[0])

    if args.gen_output_highcharts_batch:
        gen_output_highcharts_batch()
    if args.output_highcharts_atom:
        output_highcharts_atom(args.output_highcharts_atom[0])

    if args.gen_output_worddocdensity_batch:
        gen_output_worddocdensity_batch()
    if args.output_worddocdensity_atom:
        output_worddocdensity_atom(args.output_worddocdensity_atom[0])

    if args.gen_output_smart_ctf_batch:
        gen_output_smart_ctf_batch()
    if args.output_smart_ctf_atom:
        output_smart_ctf_atom(args.output_smart_ctf_atom[0])

    if args.del_method_related_files:
        del_method_related_files(args.del_method_related_files[0])
        
