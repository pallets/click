test:
	@cd tests; PYTHONPATH=.. py.test

upload-docs:
	$(MAKE) -C docs dirhtml
	rsync -a docs/_build/dirhtml/* flow.srv.pocoo.org:/srv/websites/click.pocoo.org/static/

.PHONY: upload-docs
