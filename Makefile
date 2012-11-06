all:
	make -C isan


test_cws:
	./cws.sh model.bin --train ~/data/seg/ctb5.test.seg --dev ~/data/seg/ctb5.test.seg

test_dag:
	./tag_path.sh model.bin --train ~/lattice/train.lat --dev ~/lattice/test.lat --iteration=20 --beam_width=8

test_dep:
	./parsing.sh model.bin --train test/ctb5.test.txt --dev test/ctb5.test.txt


basic_test:
	./cws.sh model.bin --train ~/data/seg/ctb5.test.seg --dev ~/data/seg/ctb5.test.seg --iteration=1
	./parsing.sh model.bin --train test/ctb5.test.txt --dev test/ctb5.test.txt --iteration=1
