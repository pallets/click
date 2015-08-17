test:
	@cd tests; PYTHONPATH=.. py.test --tb=short

upload-docs:
	$(MAKE) -C docs dirhtml
	rsync -a docs/_build/dirhtml/* flow.srv.pocoo.org:/srv/websites/click.pocoo.org/static/

release:
	python setup.py sdist bdist_wheel upload

.PHONY: upload-docs
