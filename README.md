# ALCARECO-statistics
Script written by [@jozzez1](https://github.com/jozzez1) to collect ALCARECO statistics.

## Usage

Modify the DATASETMASK in the script.

./test.py > Output.txt

This will create one additional file, called EmptyDatasets.txt which contains datasets with either no files or zero events (only the lumi header).

Output.txt has 4 columns:
<DatasetName> <Number of events> <Total dataset size (MiB)> <total length of all the runs (s)>

then run

cat Output.txt | awk '{print $1, $3*1024/$2, $2/$4}' > Result.txt

to get the final means:
<DatasetName> <Mean event size (kiB)> <mean even rate (s)>