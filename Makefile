READMES = README.md $(wildcard */README.md)
NOTES   = NOTE.md   $(wildcard */NOTE.md  )
TODOS   = TODO.md   $(wildcard */TODO.md  )
ALL_DOCS_HTML = $(subst .md,.html, $(READMES) $(NOTES) $(TODOS))

all: docs figs
docs: $(ALL_DOCS_HTML)
figs:

img/dark-field.tif: raw/img/2014-09-11/0.010surf_0.5-aq_10-hz_60-s_20-hrs-inc_1to1000dilut_r0s1f0_bf1.tif
	cp $< $@

img/fluor-fs46.tif: raw/img/2014-09-11/0.010surf_0.5-aq_10-hz_60-s_20-hrs-inc_1to1000dilut_r0s1f0_yellow.tif
	cp $< $@

pandoc_recipe_md2html = \
pandoc -f markdown -t html5 -s \
       --highlight-style pygments --mathjax \
       --toc --toc-depth=4 \
       --css static/main.css \
    <$< >$@
%/README.html: %/README.md
	$(pandoc_recipe_md2html)
%/NOTEBOOK.html: %/NOTES.md
	$(pandoc_recipe_md2html)
%/TODO.html: %/TODO.md
	$(pandoc_recipe_md2html)
%.html: %.md
	$(pandoc_recipe_md2html)

clean:
	rm -f $(ALL_DOCS_HTML)
