check: .build/dev_requirements.timestamp
	.build/venv/bin/flake8 papyrus

tests: .build/dev_requirements.timestamp
	.build/venv/bin/nosetests

clean:
	rm -rf .build

.build/venv.timestamp:
	mkdir -p $(dir $@)
	python3 -m venv .build/venv
	touch $@

.build/dev_requirements.timestamp: .build/venv.timestamp dev_requirements.txt
	.build/venv/bin/pip install -r dev_requirements.txt
	touch $@
