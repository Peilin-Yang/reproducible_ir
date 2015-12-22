# -*- coding: utf-8 -*-
import os,sys
import math
import numpy as np
import argparse
import json
import csv
from operator import itemgetter
from inspect import currentframe, getframeinfo
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

reload(sys)
sys.setdefaultencoding('utf-8')

class Plots(object):
    """
    Plot the results.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_paths):
        # we can plot multiple collections on one canvas
        self.collection_paths = collection_paths

    def check_valid_path(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Plots]:collection path ' + collection_path + ' does not exist....'
            exit(1)

        self.performance_root = os.path.join(self.corpus_path, 'performances')
        if not os.path.exists(self.performance_root):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Plots]:performance path ' + self.performance_root + ' does not exist....'
            exit(1)

    def load_optimal_performance(self, evaluation_method='map', query_part='title'):
        data = []
        with open('g.json') as f:
            j = json.load(f)
            for m in j['methods']:
                if not 'formal_name' in m:
                    continue
                with open(os.path.join(self.performance_root, query_part+'-'+m['name'])) as pf:
                    all_performance = json.load(pf)
                    required = all_performance[evaluation_method]
                    data.append( (m['name'], m['formal_name'], m['year'], 
                        required['max']['value'], required['max']['para']) )
        data.sort(key=itemgetter(2))
        return data
 
    def plot_optimal_for_single_collection(self, collection_path, ax=None, 
            evaluation_method='map', query_part='title'):
        self.check_valid_path(collection_path)
        data = self.load_optimal_performance(evaluation_method, query_part)

        markers = ['.', '+', 'v', 'h', 's', 'd', 
            '1', '8', 'p', '*', 'o', 
            'H', 'D', 'x', '2', '>']
        marker_idx = 0
        xticks_label = []
        xticks_value = []
        for d in data:
            str_year = str(d[2])[2:]+'\''
            if str_year not in xticks_label:
                xticks_label.append(str_year)
                xticks_value.append(d[2])
            ax.plot(d[2], d[3], markers[marker_idx], label=d[1])
            marker_idx += 1
            #print feature_label+':'+evaluation_method+':'+str(yaxis)
        ax.set_title(collection_path.split('/')[-1])
        ax.set_xlim([data[0][2]-1, data[-1][2]+1])
        ax.set_xticks(xticks_value)
        ax.set_xticklabels(xticks_label, rotation=40)

    def plot_optimal_for_all_collections(self, 
            evaluation_method='map', query_part='title'):
        num_cols = 2
        num_rows = int(math.ceil(len(self.collection_paths)/num_cols))
        size = 4
        fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, 
            sharey=False, figsize=(size*num_cols, size*num_rows))
        font = {'size' : 16}
        plt.rc('font', **font)
        row_idx = 0
        col_idx = 0
        #print self.collection_paths
        for collection in self.collection_paths:
            if num_rows > 1:
                ax = axs[row_idx][col_idx]
            else:
                ax = axs[col_idx]
            self.plot_optimal_for_single_collection(collection, ax, 
                evaluation_method, query_part)
            col_idx += 1
            if col_idx >= num_cols:
                col_idx = 0
                row_idx += 1

        #fig.legend(tuple(legend_line_list), legend_list, ncol=4, loc=8, fontsize=12) # lower center    
        plot_figures_root = '../plots/'        
        if not os.path.exists(plot_figures_root):
            os.makedirs(plot_figures_root)
        output_fn = os.path.join(plot_figures_root, evaluation_method+'-'+query_part+'.eps')
        plt.savefig(output_fn, format='eps', bbox_inches='tight', dpi=100)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--plot_optimal",
        nargs='+',
        help="plots the optimal performances for all collections")

    args = parser.parse_args()

    if args.plot_optimal:
        #print args.plot_optimal
        Plots(collection_paths=args.plot_optimal).plot_optimal_for_all_collections()


