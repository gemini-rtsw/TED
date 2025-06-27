for index in $(curl -s http://localhost:9200/_cat/indices/.ds-*?h=index); do
  curl -X PUT "http://localhost:9200/$index/_settings" -H 'Content-Type: application/json' -d'
    {
	        "index": {
		      "max_result_window": 50000
		          }
      }'
done
