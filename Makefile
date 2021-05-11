VENV := .env

all: venv

$(VENV)/bin/activate: requirements.txt
	python -m venv ${VENV}
	./$(VENV)/bin/python -m pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt

venv: $(VENV)/bin/activate

test: venv
	./$(VENV)/bin/python -m pytest --pdb -s

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

deploy: venv
	cdk deploy

synth: venv
	cdk synth --no-staging > template.yaml

.PHONY: all venv test clean deploy synth