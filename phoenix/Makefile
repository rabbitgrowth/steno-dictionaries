topics := $(wildcard topics/*.json5)

all: phoenix.dicp topics.json

phoenix.dicp: $(topics)
	grep -h '^// Delete: ' $^ | cut -c 12- | jq -R | jq -s '{source: "phoenix.json", add: {}, delete: .}' >phoenix.dicp

topics.json: $(topics)
	echo $^ | xargs -n1 json5 | jq -s add >topics.json
