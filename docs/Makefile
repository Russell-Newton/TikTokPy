# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= -T -E
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# This is a way to see if the current OS is windows. $(OS) is empty in tox, so this is the solution
ifeq ($(shell echo "check_quotes"),"check_quotes")
	RM_CLEAN_AUTOSUMMARY=if exist "$(SOURCEDIR)\generated" rmdir /q /s "$(SOURCEDIR)\generated"
else
	RM_CLEAN_AUTOSUMMARY=rm -rf ./$(SOURCEDIR)/generated/
endif

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	$(RM_CLEAN_AUTOSUMMARY)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
