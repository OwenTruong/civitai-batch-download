install: uninstall
	pip3 install .

test1:
	civitdl 123456 '78901,23456' ./test/models/test1

test2:
	civitdl ./test/batchtest1.txt ./test/models/test2

test3:
#	civitconfig sorter -a test3 ./custom/sort.py
# civitconfig alias -a @test ./test
# civitconfig alias -a @test3 @test/models/test3
	civitdl 191977 @test3/default
	civitdl 123456 @test3/alphabet -s ./custom/sort.py
	civitdl 78901 @test3/test3 -s test3
	civitdl 23456 @test3/tags -s tags

errortest1:
	civitdl batchfile ./test/errortest1.txt ./test/models/test2

test: install test1 test2


clean:
	rm -rf **/*.egg-info
	rm -rf dist build
	rm -rf ./test/models

uninstall: clean
	pip3 uninstall civitdl -y
