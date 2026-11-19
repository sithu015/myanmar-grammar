PY ?= python3

.PHONY: test selftest e2e hooks

test: selftest e2e
	$(PY) -B scripts/test_nlp_tools.py

selftest:
	$(PY) scripts/decide.py --self-test
	$(PY) scripts/project_mypos_hd.py --self-test
	$(PY) scripts/validate_nlp_corpus.py --self-test
	$(PY) scripts/corpus_chunk_and_remediate.py --self-test
	$(PY) scripts/legal70k_audit.py --self-test

e2e:
	$(PY) -B scripts/test_e2e_pipeline.py

hooks:
	install -m 755 scripts/pre-commit.sh .git/hooks/pre-commit
	@echo "pre-commit hook installed"
