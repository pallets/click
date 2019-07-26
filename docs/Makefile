# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = Jinja
SOURCEDIR     = .
BUILDDIR      = _build
DASHDIR       = ${BUILDDIR}/dashdoc

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

dashdoc: html
	python doc2dash-userguide.py \
		--name="Click" \
		--destination="$(DASHDIR)" \
		--index-page="index.html" \
		--icon="$(SOURCEDIR)/_static/click-logo.png" \
		--online-redirect-url="http://click.palletsprojects.com/" \
		--force \
		--verbose \
		"$(BUILDDIR)/html"

	tar --exclude=".DS_Store" -C "$(DASHDIR)" -czf "${DASHDIR}/Click.tgz" Click.docset

clean:
	rm -r "$(BUILDDIR)"

.PHONY: help Makefile dashdoc clean
