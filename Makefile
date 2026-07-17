.PHONY: all build push test build-base push-base check-design

VER := $(shell git branch --show-current | tr '/' '-')
GIT_VER := $(shell git describe --tags --always --match 'v[0-9]*' 2>/dev/null || git rev-parse --short HEAD)
IMAGE := talebook/talebook:$(VER)
REPO1 := talebook/talebook:latest
REPO2 := talebook/calibre-webserver:latest
TAG1 := talebook/talebook:server-side-render
TAG2 := talebook/talebook:server-side-render-$(VER)
BASE := talebook/talebook-base

all: lint-py-fix build up

init:
	pip3 install -r requirements.txt -r requirements-test.txt
	#python3 -m pip install --upgrade pip
	#uv sync

build: test build-spa build-ssr

BASE_VER := 8.6
BASE_PLATFORMS ?= linux/amd64,linux/arm64,linux/arm/v7

# 基础镜像：build-base 只做本机架构验证；push-base 使用 buildx 发布多架构版本标签。
# 主 Dockerfile 仍固定在已发布的 talebook/talebook-base:8.5，待 8.6 发布后再单独切换。
build-base:
	docker build -f Dockerfile.base --build-arg BUILD_COUNTRY=CN -t $(BASE):latest -t $(BASE):$(BASE_VER) .

push-base:
	docker buildx build -f Dockerfile.base --build-arg BUILD_COUNTRY=CN --platform $(BASE_PLATFORMS) -t $(BASE):latest -t $(BASE):$(BASE_VER) --push .

build-spa:
	docker build --no-cache=false --build-arg BUILD_COUNTRY=CN --build-arg GIT_VERSION=$(GIT_VER) \
		-f Dockerfile -t $(IMAGE) -t $(REPO1) --target production -t $(REPO2) .

build-ssr:
	docker build --no-cache=false --build-arg BUILD_COUNTRY=CN --build-arg GIT_VERSION=$(GIT_VER) \
		-f Dockerfile -t $(TAG1) -t $(TAG2) --target production-ssr .

build-dev:
	docker build --no-cache=false --build-arg BUILD_COUNTRY=CN \
		-f Dockerfile -t talebook/talebook:dev --target dev .

push:
	docker push $(IMAGE)
	docker push $(REPO1)
	docker push $(REPO2)

test:
	rm -f unittest.log
	docker build --build-arg BUILD_COUNTRY=CN -t talebook/test --target test -f Dockerfile .
	docker run --rm --name=talebook-docker-test -v "$$PWD":"$$PWD" -w "$$PWD" talebook/test pytest --log-file=unittest.log --log-level=INFO tests

lint-ui:
	npm ci
	cd app && npm run lint

lint-py:
	ruff check ./webserver --no-cache
	ruff format --diff ./webserver --output-format concise --no-cache

lint-py-fix:
	ruff check ./webserver --fix
	ruff format ./webserver

check-i18n:
	uv run check_i18n_translation_missing.py
	uv run check_i18n_translation_useless.py

check-design:
	python3 scripts/check_design_docs.py

pytest:
	pytest tests -v --cov=webserver --cov-report=term-missing

testv:
	coverage run -m unittest
	coverage report --include "*talebook*"

testvv: testv
	coverage html -d ".htmlcov" --include "*talebook*"
	cd ".htmlcov" && python3 -m http.server 7777

up:
	docker compose up

down:
	docker compose stop

dev: build-dev
	docker-compose -f docker-compose.dev.yml up

dev-ui:
	cd app && npm run dev
