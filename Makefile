test:
	bin/pytest
	bin/black --check original/src/
	bin/flake8 original/src/

beautiful:
	bin/isort -y -rc fews_3di/ original/src/
	bin/black fews_3di/ original/src/
