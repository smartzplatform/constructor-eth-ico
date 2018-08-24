.PHONY: ganache.pid flatten_contract

node_modules:
	npm install

ganache.pid: node_modules
	./node_modules/.bin/ganache-cli -u 0 -u 1 -u 2 -u 3 -u 4 -u 5 --gasLimit 1000000000000000 -e 100000000 --gasPrice 200 > /dev/null & echo $$! > $@
	sleep 2

test: node_modules ganache.pid
	./node_modules/.bin/truffle test

flatten_contract:
	./node_modules/.bin/truffle-flattener contracts/ICO.sol > smartz/flattened_contract.sol

build_contract:
	python smartz/gen.py > smartz/.final_constructor.py
	node_modules/smartz-sdk/bin/run-constructor.py construct --fields-json {} smartz/.final_constructor.py  > out.sol
	node_modules/.bin/solcjs -o bin/contracts  --abi  out.sol

clean: ganache.pid
	kill -9 `cat $<` && rm $<
