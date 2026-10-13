#!/bin/sh
# Keep logs for 1 year: roll over monthly, delete indices 365 days after rollover.
curl -X PUT "${HOST2_IP}:${ES1_HTTP_PORT}/_ilm/policy/ted-logs?pretty" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": { "max_age": "30d", "max_primary_shard_size": "50gb" }
        }
      },
      "delete": {
        "min_age": "365d",
        "actions": { "delete": {} }
      }
    }
  }
}
'

# Move existing log indices to the new policy.
curl -X PUT "${HOST2_IP}:${ES1_HTTP_PORT}/.ds-logs-*/_settings?pretty" -H 'Content-Type: application/json' -d'
{ "index.lifecycle.name": "ted-logs" }
'
