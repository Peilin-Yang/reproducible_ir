import query

query = [
  {
    "name": "trec7",
    "query_class": query.trec7_query,
    "qf_path": "../TREC-Adhoc/qry/Adhoc/topics.351-400",
    "cnt": 50,
    "qf_parts": ['title', 'desc', 'narr', 'title+desc', 'title+desc+narr' ],
    "index_path": "../index/disk45",
    "qrel_program": ["../TREC-Adhoc/bin/trec_eval", "-m", "all_trec", "-q"],
    "qrel_path": "../TREC-Adhoc/qrel/Adhoc/qrels.trec7",
  },
  {
    "name": "trec8",
    "query_class": query.trec8_query,
    "qf_path": "../TREC-Adhoc/qry/Adhoc/topics.401-450",
    "cnt": 50,
    "qf_parts": ['title', 'desc', 'narr', 'title+desc', 'title+desc+narr' ],
    "index_path": "../index/disk45",
    "qrel_program": ["../TREC-Adhoc/bin/trec_eval", "-m", "all_trec", "-q"],
    "qrel_path": "../TREC-Adhoc/qrel/Adhoc/qrels.trec8.adhoc.parts1-5",
  },
  {
    "name": "wt2g",
    "query_class": query.wt2g_query,
    "qf_path": "../TREC-Adhoc/qry/Adhoc/topics.401-450",
    "cnt": 50,
    "qf_parts": ['title', 'desc', 'narr', 'title+desc', 'title+desc+narr' ],
    "index_path": "../index/wt2g",
    "qrel_program": ["../TREC-Adhoc/bin/trec_eval", "-m", "all_trec", "-q"],
    "qrel_path": "../TREC-Adhoc/qrel/Adhoc/qrels.trec8.small_web",
  }
]