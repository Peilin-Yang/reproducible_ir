import sys,os
import re
import codecs
import csv
import shutil
import argparse
import inspect
import subprocess
import shlex

from bs4 import BeautifulSoup
import ArrayJob

reload(sys)
sys.setdefaultencoding('utf-8')


def gen_batch_framework(para_label, batch_pythonscript_para, all_paras, \
        quote_command=False, memory='2G', max_task_per_node=50000, num_task_per_node=10):

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


def remove_after_10000():
  d = set()
  with open('ql_baseline_from_ben_server_full') as f:
    for line in f:
      line = line.strip()
      if line:
        row = line.split()
        qid = row[0]
        docid = row[2]
        rank = int(row[3])
        if rank < 10001:
          d.add(docid)

  collection_root = 'dump_subset_collection'
  for fn in os.listdir(collection_root):
    if fn not in d:
      os.remove( os.path.join(collection_root, fn) )

def remove_http_header():
    raw_root = 'raw'
    output_root = 'without_http_header'
    if not os.path.exists(output_root):
      os.makedirs(output_root)

    for fn in os.listdir(raw_root):
      with codecs.open( os.path.join(raw_root, fn), 'rb', 'utf-8' ) as f:
          with codecs.open( os.path.join(output_root, fn), 'wb', 'utf-8' ) as o:
              warc_header_meet = False
              idx = 1
              for line in f:
                  if idx == 1:
                      o.write(line)
                  else:
                      if not warc_header_meet:
                          strip_line = line.strip()
                          if not strip_line:
                              warc_header_meet = True
                              continue
                      if warc_header_meet:
                          o.write(line)
                  idx += 1

def remove_empty_docno():
    _root = 'without_http_header'
    for fn in os.listdir(_root):
      with codecs.open( os.path.join(_root, fn), 'rb', 'utf-8' ) as f:
        first_line = f.readline()
        m = re.search(r'<docno>(.*)</docno>', first_line)
        if m:
          if not m.groups()[0].strip():
            print '[NO DOCNO]'+fn
        else:
          print '[NO DOCNO]'+fn

          
def gen_batch_extract_text():
    all_paras = []

    input_root = 'without_http_header'
    output_root = 'pure_text'
    if not os.path.exists(output_root):
      os.makedirs(output_root)

    for fn in os.listdir(input_root):
      if not os.path.exists( os.path.join(output_root, fn) ):
        all_paras.append( (os.path.join(input_root, fn), os.path.join(output_root, fn)) )

    print len(all_paras)
    gen_batch_framework('extract_text', 'd2', all_paras)


def extract_text_atom(para_file):
    with open(para_file) as f:
        reader = csv.reader(f)
        for row in reader:
            input_fn = row[0]
            output_fn = row[1]
            extract_text(input_fn, output_fn)

def visible(element):
    if element.parent.name in ['style', 'script', '[document]']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True

def extract_text(input_fn, output_fn):
    with codecs.open( input_fn, 'rb', 'utf-8' ) as f:
      with codecs.open( output_fn, 'wb', 'utf-8' ) as o:
        o.write('<DOC>\n')
        o.write(f.readline())
        o.write('<TEXT>\n')
        soup = BeautifulSoup(f, 'lxml')
        texts = soup.findAll(text=True)
        visible_texts = filter(visible, texts)
        o.write('\n'.join(visible_texts))
        o.write('</TEXT>\n')
        o.write('</DOC>\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--remove_after_10000",
        action='store_true',
        help="Remove the docs after ranking 10000")

    parser.add_argument("-b", "--remove_http_header",
        action='store_true',
        help="Remove the HTTP header of the docs")

    parser.add_argument("-c", "--remove_empty_docno",
        action='store_true',
        help="Remove the docs without docno")

    parser.add_argument("-d1", "--gen_batch_extract_text",
        action='store_true',
        help="Extract the text from the documents")
    parser.add_argument("-d2", "--extract_text_atom",
        nargs=1,
        help="Extract the text from the documents")

    args = parser.parse_args()

    if args.remove_after_10000:
        remove_after_10000()

    if args.remove_http_header:
        remove_http_header()

    if args.remove_empty_docno:
        remove_empty_docno()

    if args.gen_batch_extract_text:
        gen_batch_extract_text()
    if args.extract_text_atom:
        extract_text_atom(args.extract_text_atom[0])
