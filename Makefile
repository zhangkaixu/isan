all:
	make -C isan


test_cws:
	./cws.sh model.bin --train ~/data/seg/ctb5.test.seg --dev ~/data/seg/ctb5.test.seg
