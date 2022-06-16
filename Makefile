install: bin/activate bin/run-fews-3di


clean:
	rm -rf bin include lib pyvenv.cfg


# A virtualenv creates bin/activate
bin/activate:
	python3 -m venv .


bin/run-fews-3di: requirements.txt setup.py setup.cfg
	bin/pip install -r requirements.txt


test: install
	bin/flake8 fews_3di/
	bin/black --check fews_3di/
	bin/pytest

beautiful: install
	bin/isort fews_3di/
	bin/black fews_3di/
