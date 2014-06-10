UIFILES := $(wildcard app/gui/*.ui)
PYFILES := $(UIFILES:.ui=.py)

all: $(PYFILES)

%.py: %.ui
	pyuic4 $< --output $@
	
clean:
	rm -f *.pyc 
	rm -f app/gui/*.py*
