upload-docs:
	$(MAKE) -C docs dirhtml
	scp -r docs/_build/dirhtml/* flow.srv.pocoo.org:/srv/websites/click.pocoo.org/static/

.PHONY: upload-docs
