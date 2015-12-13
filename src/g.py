import query

query = [
  {
    "collection": "wt2g",
    "query_class": query.Query,
    "cnt": 50,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  },
  {
    "collection": "disk45",
    "query_class": query.Query,
    "cnt": 250,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  },  
  {
    "collection": "disk12",
    "query_class": query.Query,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  },   
  {
    "collection": "gov2",
    "query_class": query.Query,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  },  
  {
    "collection": "doe",
    "query_class": query.Query,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  },
  {
    "collection": "clueweb09",
    "query_class": query.ClueWebQuery,
    "cnt": 200,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  },
  {
    "collection": "clueweb12",
    "query_class": query.ClueWebQuery,
    "cnt": 100,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q'
  }
]
