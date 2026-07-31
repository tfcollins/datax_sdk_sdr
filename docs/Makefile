SPHINXBUILD ?= python -m sphinx
SOURCEDIR   = .
BUILDDIR    = _build

.PHONY: html linkcheck clean

html:
	$(SPHINXBUILD) -W -b html $(SOURCEDIR) $(BUILDDIR)/html

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(SOURCEDIR) $(BUILDDIR)/linkcheck

clean:
	rm -rf $(BUILDDIR)
