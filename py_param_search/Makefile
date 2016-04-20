SOURCE_FILE=assert_ex
LOG_FILE=log

.PHONY: clean

clean_here:
	@rm -f $(SOURCE_FILE)_*
	@rm -f $(LOG_FILE)_*
	
SUBDIRS = c_src 

clean:
	@for dir in $(SUBDIRS); do \
         make -s clean -C  $$dir; \
    done
