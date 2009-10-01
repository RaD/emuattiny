PY=$(wildcard *.py)
PYC=$(patsubst %.py,%.pyc,$(PY))

all:
	echo "Usage:\n\tmake clean\n\tmake compile"

clean:
	rm -f $(PYC) *~

compile: $(PYC)

%.pyc: %.py
	py_compilefiles $<
