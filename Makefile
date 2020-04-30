test:
	bin/pytest

beautiful:
	bin/isort -y -rc fews_3di/
	bin/black fews_3di/
