lint:
	poetry run flake8 src/

test:
	poetry run pytest tests/

bump-patch:
	poetry run bumpversion patch

bump-minor:
	poetry run bumpversion minor

bump-major:
	poetry run bumpversion major
