CARGO ?= cargo
RUN_BIN ?= router_demo
CHECK_FLAGS ?=
TEST_FLAGS ?=
ARGS ?=
SELF_CHECK_ARGS ?=

.PHONY: run check fmt lint test self-check

run:
	$(CARGO) run -p bbs_sandbox --bin $(RUN_BIN) -- $(ARGS)

fmt:
	$(CARGO) fmt --all -- --check

lint:
	$(CARGO) clippy --workspace --all-targets -- -D warnings

check: fmt lint
	$(CARGO) check --workspace --all-targets $(CHECK_FLAGS)

self-check:
	$(CARGO) run -p bbs_sandbox --bin router_demo -- $(SELF_CHECK_ARGS) --check

test:
	$(CARGO) test --workspace $(TEST_FLAGS)
	$(MAKE) self-check SELF_CHECK_ARGS="$(SELF_CHECK_ARGS)"
