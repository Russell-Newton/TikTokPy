# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

ifeq ($(OS),Windows_NT)
	RM_CLEAN_AUTOSUMMARY=if exist "$(SOURCEDIR)\generated" rmdir /q /s "$(SOURCEDIR)\generated"
else
	RM_CLEAN_AUTOSUMMARY=rm -rf $(SOURCEDIR)/generated
endif

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	$(RM_CLEAN_AUTOSUMMARY)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
