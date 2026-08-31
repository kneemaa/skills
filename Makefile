GO_DIR := .github/actions/lint-semantic-pull-request/scripts

.PHONY: check validate go-check

check: validate go-check ## Run everything CI runs

validate: ## Validate manifests, skills, and relative links (needs: pip install pyyaml)
	python3 .github/scripts/validate-plugin.py

go-check: ## Format-check, vet, and test the Go action helper
	cd $(GO_DIR) && \
		{ test -z "$$(gofmt -l .)" || { gofmt -l .; echo "run gofmt -w ."; exit 1; }; } && \
		go vet ./... && \
		go test ./...
