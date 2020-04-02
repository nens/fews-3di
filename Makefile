test:
	bin/pytest
	bin/black --check fews_3di/ original/src/
	bin/flake8 fews_3di/ original/src/
	bin/mypy fews_3di/

beautiful:
	bin/isort -y -rc fews_3di/ original/src/
	bin/black fews_3di/ original/src/
