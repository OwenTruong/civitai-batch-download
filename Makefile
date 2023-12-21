install: uninstall
	pip3 install .

test1:
	civitdl 123456 '78901,23456' ./test/models/test1 -v

test2:
	civitdl ./test/batchtest1.txt ./test/models/test2 -v

test3:
	# civitconfig sorter -a test3 ./custom/sort.py
	# civitconfig alias -a @test ./test
	# civitconfig alias -a @test3 @test/models/test3
	civitdl 191977 @test3/default -v
	civitdl 123456 @test3/alphabet -s ./custom/sort.py -v
	civitdl 78901 @test3/test3 -s test3 -v
	civitdl 23456 @test3/tags -s tags -v
	civitconfig default --with-prompt
	civitdl 80848 @test3/test-prompt-1 -v
	civitconfig default --no-with-prompt
	civitdl 80848 @test3/test-prompt-2 -v

test4:
	civitdl 80848 ./test/models/test4/with-prompt -v --with-prompt
	civitdl 80848 ./test/models/test4/without-prompt -v --no-with-prompt

errortest1:
	civitdl batchfile ./test/errortest1.txt ./test/models/test2 -d -v

test: install test1 test2 test4


clean:
	rm -rf **/*.egg-info
	rm -rf dist build
	rm -rf ./test/models

uninstall: clean
	pip3 uninstall civitdl -y
