import query

query = [ 
  {
    "collection": "wt2g",
    "query_class": query.Query,
    "cnt": 50,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },
  {
    "collection": "disk45",
    "query_class": query.Query,
    "cnt": 250,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },  
  {
    "collection": "disk12",
    "query_class": query.Query,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },   
  {
    "collection": "gov2",
    "query_class": query.Query,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },
  {
    "collection": "clueweb09",
    "query_class": query.ClueWebQuery,
    "cnt": 200,
    "qf_parts": ['title'],
    "qrel_program": 'gdeval.pl',
    "main_metric": "ERR@20"
  },
  {
    "collection": "clueweb12",
    "query_class": query.ClueWebQuery,
    "cnt": 100,
    "qf_parts": ['title'],
    "qrel_program": 'gdeval.pl',
    "main_metric": "ERR@20"
  }
]
