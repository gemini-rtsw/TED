for index in $(curl -s http://${HOST2_IP}:${ES1_HTTP_PORT}/_cat/indices/.ds-*?h=index); do
  curl -X PUT "http://${HOST2_IP}:${ES1_HTTP_PORT}/$index/_settings" -H 'Content-Type: application/json' -d'
    {
	        "index": {
		      "max_result_window": 50000
		          }
      }'
done
