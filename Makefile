.PHONY: ganache.pid

node_modules:
	npm install

ganache.pid:
	./node_modules/.bin/ganache-cli -u 0 -u 1 -u 2 -u 3 -u 4 -u 5 --gasLimit 1000000000000000 -e 100000000 --gasPrice 200 > /dev/null & echo $$! > $@
	sleep 2

test: ganache.pid
	./node_modules/.bin/truffle test || kill -9 `cat $<` && rm $<
