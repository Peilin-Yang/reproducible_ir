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
from pylab import *
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import g

reload(sys)
sys.setdefaultencoding('utf-8')

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams['ps.useafm'] = True
matplotlib.rcParams['pdf.use14corefonts'] = True
matplotlib.rcParams['text.usetex'] = True

class Plots(object):
    """
    Plot the results.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_paths, collection_names=None):
        # we can plot multiple collections on one canvas
        self.collection_paths = collection_paths
        self.collection_names = collection_names

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
                    try:
                        required = all_performance[evaluation_method]
                    except:
                        required = all_performance['err_cut_20']
                    data.append( (m['name'], m['formal_name'], m['year'], 
                        required['max']['value'], required['max']['para']) )
        data.sort(key=itemgetter(2))
        return data
 
    def plot_optimal_for_single_collection(self, collection_path, 
            legend_line_list, legend_list, add_legend=False, ax=None, 
            evaluation_method='map', query_part='title', 
            show_xlabel=True, show_ylabel=True, collection_name=None):
        self.check_valid_path(collection_path)
        data = self.load_optimal_performance(evaluation_method, query_part)

        markers = ['o', 'h', 'v', 'p', 's', 'd', 
            '3', '4', '.', 'x', 'h', 
            '*', '^', '<', '>', '8']
        marker_idx = 0
        xticks_label = []
        xticks_value = []
        for d in data:
            str_year = str(d[2])[2:]+'\''
            if str_year not in xticks_label:
                xticks_label.append(str_year)
                xticks_value.append(d[2])
            l, = ax.plot(d[2], d[3], markers[marker_idx], markersize=10, label=d[1])
            if add_legend:
                legend_line_list.append(l)
                legend_list.append(d[1])
            marker_idx += 1
            #print feature_label+':'+evaluation_method+':'+str(yaxis)
        if collection_name:
            ax.set_title(collection_name)
        else:
            ax.set_title(collection_path.split('/')[-1])
        if show_xlabel:
            ax.set_xlabel('Publish Year')
        if show_ylabel:
            ax.set_ylabel(evaluation_method.upper())
        ax.set_xlim([data[0][2]-1, data[-1][2]+1])
        ax.set_xticks(xticks_value)
        ax.set_xticklabels(xticks_label, rotation=90)
        ax.grid('on')

    def plot_optimal_for_all_collections(self, 
            evaluation_method='map', query_part='title'):
        num_cols = 2
        num_rows = int(math.ceil(len(self.collection_paths)/num_cols))
        size = 4
        fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, 
            sharey=False, figsize=(size*num_cols, size*num_rows+3)) # +1 for legend!!!
        font = {'size' : 12}
        plt.rc('font', **font)
        row_idx = 0
        col_idx = 0
        #print self.collection_paths
        legend_line_list = []
        legend_list = []
        for i, collection in enumerate(self.collection_paths):
            if num_rows > 1:
                ax = axs[row_idx][col_idx]
            else:
                ax = axs[col_idx]
            if row_idx > 1:
                evaluation_method = 'ERR@20'
            print row_idx, evaluation_method
            self.plot_optimal_for_single_collection(collection, 
                legend_line_list, legend_list, 
                row_idx == 0 and col_idx == 0, 
                ax, 
                evaluation_method, query_part, 
                row_idx==num_rows-1, col_idx==0,
                self.collection_names[i] if self.collection_names else None)
            col_idx += 1
            if col_idx >= num_cols:
                col_idx = 0
                row_idx += 1

        lgd = fig.legend(tuple(legend_line_list), legend_list, ncol=5, 
            loc='lower center', bbox_to_anchor=(0.45, -0.01), fontsize=12,
            frameon=False) # lower center    
        plot_figures_root = '../plots/'        
        if not os.path.exists(plot_figures_root):
            os.makedirs(plot_figures_root)
        output_fn = os.path.join(plot_figures_root, evaluation_method+'-'+query_part+'.eps')
        fig.savefig(output_fn, format='eps', bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=100)



    def load_optimal_performance_for_barchart(self, evaluation_method='map', query_part='title'):
        data = []
        methods = ['f2log', 'lowerboundingbm25+', 
            'lowerboundingpiv+', 'sigir2013tfidf',
            'twostage', 'f3log',
            'lowerboundingpl2+', 'lgd'
        ]
        all_methods = []
        with open('g.json') as f:
            j = json.load(f)
            for required_m in methods:
                for m in j['methods']:
                    if m['name'] == required_m:
                        all_methods.append(m)

        for m in all_methods:
            with open(os.path.join(self.performance_root, query_part+'-'+m['name'])) as pf:
                all_performance = json.load(pf)
                try:
                    required = all_performance[evaluation_method]
                except:
                    required = all_performance['err_cut_20']
                data.append( (m['name'], m['formal_name'], m['year'], 
                    required['max']['value'], required['max']['para']) )
        return data
 
    def plot_single_barchart(self, collection_path, 
            legend_line_list, legend_list, add_legend=False, ax=None, 
            evaluation_method='map', query_part='title', 
            show_xlabel=True, show_ylabel=True, collection_name=None):
        self.check_valid_path(collection_path)
        data = self.load_optimal_performance_for_barchart(evaluation_method, query_part)
        print data
        patterns = ('-', '//', 'x', '\\', '+', 'o', '/', '.')
        colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'w')
        width = 0.65
        for i, d in enumerate(data):
            xaxis = [i]
            yaxis = d[3]
            b = ax.bar(xaxis, yaxis, width, color='c', hatch=patterns[i])
            if add_legend:
                legend_list.append(d[1])
                legend_line_list.append(b)

        #marker_idx += 1
        #print feature_label+':'+evaluation_method+':'+str(yaxis)
        if collection_name:
            ax.set_title(collection_name)
        else:
            ax.set_title(collection_path.split('/')[-1])
        if show_ylabel:
            ax.set_ylabel(evaluation_method.upper())
        #ax.set_xlim([data[0][2]-1, data[-1][2]+1])
        #ax.set_xticks(xticks_value)
        #ax.set_xticklabels(xticks_label, rotation=90)
        #ax.grid('on')

    def plot_barchart_for_all_collections(self, 
            evaluation_method='map', query_part='title'):
        num_cols = 2
        num_rows = int(math.ceil(len(self.collection_paths)/num_cols))
        size = 3
        fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, 
            sharey=False, figsize=(size*num_cols, size*num_rows+2)) # +1 for legend!!!
        font = {'size' : 12}
        plt.rc('font', **font)
        plt.tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom='off',      # ticks along the bottom edge are off
            top='off',         # ticks along the top edge are off
            labelbottom='off') # labels along the bottom edge are off
        row_idx = 0
        col_idx = 0
        #print self.collection_paths
        legend_line_list = []
        legend_list = []
        for i, collection in enumerate(self.collection_paths):
            if num_rows > 1:
                ax = axs[row_idx][col_idx]
            else:
                ax = axs[col_idx]
            if row_idx > 1:
                evaluation_method = 'ERR@20'
            #print row_idx, evaluation_method
            self.plot_single_barchart(collection, 
                legend_line_list, legend_list, 
                row_idx == 0 and col_idx == 0, 
                ax, 
                evaluation_method, query_part, 
                row_idx==num_rows-1, col_idx==0,
                self.collection_names[i] if self.collection_names else None)
            col_idx += 1
            if col_idx >= num_cols:
                col_idx = 0
                row_idx += 1
        print legend_line_list, legend_list
        lgd = fig.legend(tuple(legend_line_list), legend_list, ncol=4, 
            loc='lower center', bbox_to_anchor=(0.5, 0.01), fontsize=12,
            frameon=False) # lower center    
        plot_figures_root = '../plots/'        
        if not os.path.exists(plot_figures_root):
            os.makedirs(plot_figures_root)
        output_fn = os.path.join(plot_figures_root, evaluation_method+'-'+query_part+'_bar.eps')
        fig.savefig(output_fn, format='eps', bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=100)


    def plot_single_barchart_clueweb(self, row_idx, idx, data, 
            legend_line_list, legend_list, add_legend=False, ax=None, 
            evaluation_method='map', query_part='title', 
            show_xlabel=True, show_ylabel=True, title=None):
        #self.check_valid_path(collection_path)
        #data = self.load_optimal_performance_for_barchart(evaluation_method, query_part)
        #print data
        patterns = ('-', '//', 'x', '\\', '+', 'o', '/', '.')
        colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'w')
        width = 0.8
        all_bars = []
        for i, d in enumerate(data):
            xaxis = np.asarray([i])
            yaxis = d[1]
            if idx == 1:
                b = ax.bar(xaxis+1, yaxis, width, color='c', hatch=patterns[i], label=d[0])
            if idx == 3:
                b = ax.bar(xaxis+2, yaxis, width, color='c', hatch=patterns[i], label=d[0])
            else:
                b = ax.bar(xaxis+1, yaxis, width, color='c', hatch=patterns[i], label=d[0])
            all_bars.append(b[0])
            # if add_legend:
            #     legend_list.append(d[0])
            #     legend_line_list.append(b)

        print row_idx, all_bars, [d[0] for d in data]
        if row_idx == 0:
            ax.legend(all_bars, [d[0] for d in data], 
                ncol=3, fontsize=12,frameon=False,
                loc='lower center', bbox_to_anchor=(0.5, -0.15)
                )
        #marker_idx += 1
        #print feature_label+':'+evaluation_method+':'+str(yaxis)
        ax.set_title(title, fontsize=16)
        if show_ylabel:
            ax.set_ylabel(evaluation_method.upper())
        #ax.set_xlim([data[0][2]-1, data[-1][2]+1])
        #ax.set_xticks(xticks_value)
        ax.set_xticklabels(())
        #ax.grid('on')

    def plot_barchart_for_clubweb(self, 
            evaluation_method='ERR@20', query_part='title'):
        datas = {
            'CW09': [
                ('BM25 and its variants', [('BM25', 0.089),('F2EXP', 0.099),('F2LOG', 0.1),('BM3', 0.098),('BM25+', 0.102)]),
                ('PIV and its variants', [('PIV', 0.104),('F1EXP', 0.1),('F1LOG', 0.104),('PIV+', 0.113)]),
                ('DIR and its variants', [('DIR', 0.09),('TSL', 0.09),('F3EXP', 0.101),('F3LOG', 0.109),('DIR+', 0.09)]),
                ('PL2 and its variants', [('PL2', 0.089),('PL3', 0.093),('PL2+', 0.089)])
            ],
            'CW12': [
                ('BM25 and its variants', [('BM25', 0.128),('F2EXP', 0.139),('F2LOG', 0.137),('BM3', 0.130),('BM25+', 0.137)]),
                ('PIV and its variants', [('PIV', 0.137),('F1EXP', 0.135),('F1LOG', 0.137),('PIV+', 0.141)]),
                ('DIR and its variants', [('DIR', 0.134),('TSL', 0.134),('F3EXP', 0.138),('F3LOG', 0.138),('DIR+', 0.134)]),
                ('PL2 and its variants', [('PL2', 0.116),('PL3', 0.117),('PL2+', 0.119)])
            ], 
        }
        for collection in sorted(datas):
            num_cols = 4
            num_rows = 1
            size = 6
            fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, 
                sharey=True, figsize=(size*num_cols, size*num_rows)) # +1 for legend!!!
            plt.rc('font',**{'family':'sans-serif','sans-serif':['Helvetica'], 'size': 18})
            plt.tick_params(
                axis='x',          # changes apply to the x-axis
                which='both',      # both major and minor ticks are affected
                bottom='off',      # ticks along the bottom edge are off
                top='off',         # ticks along the top edge are off
                labelbottom='off') # labels along the bottom edge are off
            row_idx = 0
            col_idx = 0
            #print self.collection_paths
            legend_line_list = []
            legend_list = []
        
            for ele in datas[collection]:
                title = ele[0]
                data = ele[1]
                if num_rows > 1:
                    ax = axs[row_idx][col_idx]
                else:
                    ax = axs[col_idx]
                #print row_idx, evaluation_method
                self.plot_single_barchart_clueweb(
                    row_idx, col_idx, data, 
                    legend_line_list, legend_list, 
                    row_idx == 0 and col_idx == 0, 
                    ax, 
                    evaluation_method, query_part, 
                    row_idx==num_rows-1, col_idx==0,
                    title)
                col_idx += 1
                if col_idx >= num_cols:
                    col_idx = 0
                    row_idx += 1
            fig.suptitle(collection, fontsize=18)
            print legend_line_list, legend_list
            # lgd = fig.legend(tuple(legend_line_list), legend_list, ncol=4, 
            #     loc='lower center', bbox_to_anchor=(0.5, 0.01), fontsize=12,
            #     frameon=False) # lower center    
            plot_figures_root = '../plots/'        
            if not os.path.exists(plot_figures_root):
                os.makedirs(plot_figures_root)
            output_fn = os.path.join(plot_figures_root, '%s_bar.eps' % collection)
            fig.savefig(output_fn, format='eps', bbox_inches='tight', dpi=100)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--plot_optimal",
        nargs='+',
        help="plots the optimal performances for all collections")

    parser.add_argument("-b", "--plot_optimal_batch",
        action='store_true',
        help="plots the optimal performances for all collections using g.py")

    parser.add_argument("-c", "--plot_optimal_barchart_batch",
        action='store_true',
        help="plots the optimal performances for all collections using g.py")

    parser.add_argument("-d", "--plot_clubweb",
        action='store_true',
        help="plots the optimal performances for all collections using g.py")

    args = parser.parse_args()

    if args.plot_optimal:
        #print args.plot_optimal
        Plots(collection_paths=args.plot_optimal).plot_optimal_for_all_collections()

    if args.plot_optimal_batch:
        #print args.plot_optimal
        collections = [os.path.join('../collections/', c['collection']) for c in g.query]
        c_names = [c['collection_formal_name'] for c in g.query]
        Plots(collections, c_names).plot_optimal_for_all_collections()

    if args.plot_optimal_barchart_batch:
        collections = [os.path.join('../collections/', c['collection']) for c in g.query]
        c_names = [c['collection_formal_name'] for c in g.query]
        Plots(collections, c_names).plot_barchart_for_all_collections()

    if args.plot_clubweb:
        collections = ['clueweb101112', 'clueweb12'] # this is supposed to only include ClueWeb collections
        c_names = [c['collection_formal_name'] for c in g.query]
        Plots(collections, c_names).plot_barchart_for_clubweb()
