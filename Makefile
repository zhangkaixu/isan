all:
	make -C isan


test_cws:
	./cws.sh model.bin --train ~/data/seg/ctb5.test.seg --dev ~/data/seg/ctb5.test.seg

test_dag:
	./tag_path.sh model.bin --train test/train1000.dlat --dev test/test.dlat --iteration=5
	#./tag_path.sh model.bin --train test/train.dlat --dev test/test.dlat --iteration=20

test_dep:
	./parsing.sh model.bin --train test/ctb5.test.txt --dev test/ctb5.test.txt

test_lat_dep:
	./lat_dep.sh model.bin --train test/train1000.dlat --dev test/test.dlat --iteration=20
	#./lat_dep.sh model.bin --train test/train.dlat --dev test/test.dlat --iteration=20

test_seq_dep:
	./seq_dep.sh model.bin --train test/train1000.dlat --dev test/test.dlat --iteration=20
	#./seq_dep.sh model.bin --train test/train.dlat --dev test/test.dlat --iteration=20

test_lat_tag:
	#./lat_tag.sh model.bin --train test/train.dlat --dev test/test.dlat --iteration=5
	./lat_tag.sh model.bin --train test/train1000.dlat --dev test/test.dlat --iteration=5

basic_test:
	./cws.sh model.bin --train ~/data/seg/ctb5.test.seg --dev ~/data/seg/ctb5.test.seg --iteration=1
	./parsing.sh model.bin --train test/ctb5.test.txt --dev test/ctb5.test.txt --iteration=1

test_msr:
	./cws.sh model.bin --train ~/data/seg/msr.training.seg --dev ~/data/seg/msr.test.seg --iteration=30

test_ctb5_parsing:
	./parsing.sh model.bin --train test/ctb5.training.txt --dev test/ctb5.test.txt --iteration=30
