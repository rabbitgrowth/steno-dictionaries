topics := $(wildcard topics/*.json5)

all: phoenix.dicp topics.json

phoenix.dicp: $(topics)
	{ \
	echo '{'; \
	echo '  "source": "phoenix.json",'; \
	echo '  "add": {},'; \
	echo '  "delete": ['; \
	grep -h '^// Delete: ' $^ | cut -c 12- | sed 's/.*/    "&",/'; \
	echo '    "WUZ/WUZ"'; \
	echo '  ]'; \
	echo '}'; \
	} >phoenix.dicp

topics.json: $(topics)
	echo $^ | xargs -n1 json5 | jq -s add >topics.json
