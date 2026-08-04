SPHINXBUILD ?= python -m sphinx
SOURCEDIR   = .
BUILDDIR    = _build
CHROME      ?= google-chrome

.PHONY: html linkcheck pdf clean

html:
	$(SPHINXBUILD) -W -b html $(SOURCEDIR) $(BUILDDIR)/html

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(SOURCEDIR) $(BUILDDIR)/linkcheck

# Single-page HTML printed to PDF by headless Chrome, so mermaid
# diagrams render exactly as on the site. The virtual-time budget
# lets the CDN mermaid module load and draw before printing. The
# cosmic theme does not style singlehtml output, so the build swaps
# in css/pdf.css for the print layout.
pdf:
	$(SPHINXBUILD) -W -b singlehtml \
	  -D html_css_files=css/pdf.css \
	  $(SOURCEDIR) $(BUILDDIR)/singlehtml
	$(CHROME) --headless=new --disable-gpu --no-sandbox \
	  --virtual-time-budget=30000 --no-pdf-header-footer \
	  --print-to-pdf=$(BUILDDIR)/datax-sdr-sdk.pdf \
	  "file://$(abspath $(BUILDDIR))/singlehtml/index.html"

clean:
	rm -rf $(BUILDDIR)
