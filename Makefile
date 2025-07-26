##
# PY-MCMAS Project Automation
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
.SHELL := bash
# .SHELLFLAGS := -euo pipefail -c
MAKEFLAGS += --warn-undefined-variables
.DEFAULT_GOAL := help

THIS_MAKEFILE := $(abspath $(firstword $(MAKEFILE_LIST)))
THIS_MAKEFILE := `python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' ${THIS_MAKEFILE}`
SRC_ROOT := $(shell dirname ${THIS_MAKEFILE})

mcmas.docker=ghcr.io/mattvonrocketstein/mcmas:v1.3.0
py.pkg_name=mcmas

export CMK_LOG_IMPORTS?=0
export MKDOCS_LISTEN_PORT=8003

.PHONY: build docs 

include .cmk/compose.mk
$(call compose.import, file=docker-compose.yml)
$(call mk.import.plugins, actions.mk docs.mk pdoc.mk py.mk )
$(call docker.import, namespace=docker.mcmas img=${mcmas.docker})
$(call docker.import, namespace=docker.pymcmas img=pymcmas file=Dockerfile)

#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

__main__: help.local

py.test: test-units smoke-test test-integrations

clean: flux.stage/clean py.clean docker.pymcmas.clean
	@# Project Clean {`py.clean docker.pymcmas.clean`}

build: flux.stage/build py.init docker.pymcmas.build
	@# Project build. `{py.build docker.pymcmas.build}`

init: flux.stage/init mk.stat docker.stat \
	py.stat py.init docs.init
	@# Project init. `{py.init docs.init}`

docs: flux.stage/doc \
	docs.init docs/api docs/schema \
	README.md CITATION.bib docs.jinja

release: pypi.release docker.mcmas.release

version: py.version
	@# Alias for py.version

test: flux.stage/test py.test #docker.pymcmas.test #lint 


# Import tox environments.
# After tox describes/manages a virtualenv, it calls this Makefile 
# from that virtualenv, passing control back to `self.*` targets in this section
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
$(call tox.import, ruff type-check docs-build venv normalize itest stest utest static-analysis)
self.normalize:
	pushd src; shed; popd; 
	autopep8 --recursive --in-place src
	isort --settings-file .isort.cfg src
	(ruff check src --fix || true)
	( docformatter --recursive --in-place --wrap-descriptions 65 \
		--wrap-summaries 65 --pre-summary-newline --make-summary-multi-line src \
		|| true )

validate lint: type-check static-analysis
self.static-analysis:
	$(call log.target, ${no_ansi}source code ${sep} flake8 and vulture)
	flake8 --config .flake8 src
	vulture src --min-confidence 90
	$(call log.target, ${no_ansi}test code ${sep} flake8 and vulture)
	flake8 --config .flake8 tests
	vulture tests --min-confidence 90
	$(call log.target, interrogate ${sep} docstring coverage follows)
	(interrogate -v src/ || true)

# integration_tests.build 
test-integrations:  ollama.serve flux.timer/itest

ollama.serve:
	$(call log.target,...)
	${io.curl} http://localhost:11434/ -s -o /dev/null \
	&& (\
		$(call log.target,ollama seems to be running already) \
	) || ($(call log.target,ollama isnt running yet) \
		&& ${make} ollama.up.detach io.wait/3 ollama.serve \
	)
self.itest:
	env | grep TOX && pytest -s -vv tests/itests

test-units: flux.timer/utest
self.units:
	env | grep TOX && pytest -s -vv tests/units

smoke-test: stest
self.stest: flux.timer/.self.stest
define .self.stest
set -x 
python -m mcmas -h
python -m mcmas tests/data/muddy_children.ispl 
python -m mcmas tests/data/card_games.ispl --json
mcmas -h
mcmas tests/data/muddy_children.ispl
mcmas --json tests/data/muddy_children.ispl
ispl --list-pydantic-models | jq .
ispl -c'print(Agent)'
ispl -c'print(Agent)'
ispl --python tests/data/minimal.py --sim
ispl --python tests/data/minimal.py -c 'print(__spec__)'
ispl --ispl tests/data/card_games.ispl | jq . |ispl --json /dev/stdin | ispl --ispl /dev/stdin --sim
ispl --analyze tests/data/minimal.ispl| jq .symbols.actions
# FIXME: breaks only in docker??
# ispl --validate tests/data/minimal.ispl| jq .validates
# ispl --validate tests/data/minimal.ispl| jq .advice
endef
$(call compose.import.script, def=.self.stest)

#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

docker.pymcmas.clean: #flux.NIY
docker.pymcmas.release: docker.mcmas.build flux.NIY
docker.pymcmas.test: docker.pymcmas.build docker.pymcmas.dispatch/self.stest
	@# Runs the normal smoke-test inside the docker-image.

# Docs related
#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

serve: docs.serve

.PHONY: README.md CITATION.bib
CITATION.bib:; ${docs.render.mirror}
README.md:; ${docs.render.mirror}

docs.test.src/%:
	@# Experimental
	griffe dump -s `dirname ${*}` -f `basename -s.py ${*}` \
	| jq ".`basename -s.py ${*}`.members[]|select(.kind==\"function\") | [[.lineno,.endlineno]]"
#make docs.test.src/tests/units/test_analyze.py
docs/api: \
	io.print.banner/docs/api \
	tox.dispatch/docs,self.api_docs \
	io.print.banner/fin-docs/api 
docs/schema: io.print.banner/docs/schema \
	docs.pynchon.render/docs/schema/index.md.j2 \
	self.gen.schema/Simulation \
	self.gen.schema/ISPL  \
	io.print.banner/fin-docs/schema
self.gen.schema/%:
	$(call log.io, ${@} ${sep} ${*} ${sep} ${cyan_flow_right})
	${trace_maybe} \
	&& set -x && ispl --schema ${*} | ${stream.peek} > docs/schema/${*}.json
self.api_docs: pdoc/mcmas
	@# Runs inside tox `docs` environment
	tree docs/api

#░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

actions.clean.img.test:
	gh run list --workflow=img-test.yml --json databaseId,createdAt \
	| ${jq} '.[] | select(.createdAt | fromdateiso8601 < now - (60*60*10)) | .databaseId' \
	| xargs -I{} gh run delete {}
	
