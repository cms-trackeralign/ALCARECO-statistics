#!/bin/env python

###############################
# Original Author: Joze Zobec #
# joze.zobec@cern.ch          #
###############################

import os
import sys
import calendar
import importlib
import sqlalchemy
import subprocess
import CondCore.Utilities.conddblib as conddb

DATASETMASK = ['/*/Run2017*TkAl*Prompt*/ALCARECO','/*/Run2017*TkAl*Express*/ALCARECO'] # datasetmasks for datasets to process
MarkFile    = 'EmptyDatasets.txt' # logfile for datasets with no files or datasets with zero events

Info        = [] # GlobalVariable with all the info -- final output

def getListOfDatasets(masks):
	cmd_out = []
	for mask in masks:
		cmd_out += os.popen('dasgoclient -query=\'dataset = %s\'' % mask).read().split()
	return cmd_out

def extractDatasetInfo(dataset, logfile):
	NEvts = 0
	Size  = 0
	cmd_out = os.popen('dasgoclient -query=\'file dataset=%s | grep file.nevents, file.size\'' % dataset).read().split('\n')
	if len(cmd_out) == 0:
		logfile.write('%s\n' % dataset)
	else:
		for out in cmd_out:
			if len(out.split()) < 1: continue
			nEvts = int(out.split()[0])
			if nEvts == 0: # skip files that contain only the lumi header
				continue
			else:
				NEvts += nEvts
				Size  += int(out.split()[1])/1048576 # convert to megabytes
		if NEvts == 0:
			logfile.write('%s\n' % dataset) # datasets with zero events in total should be in principle removed
		else:
			Info.append(['%s' % dataset, NEvts, Size, 0])

def getTime ():
	for i, info in enumerate(Info):
		runs = os.popen('dasgoclient -query=\'run dataset=%s\'' % info[0]).read().split()

		con = conddb.connect(url = conddb.make_url())
		session = con.session()
		RunInfo = session.get_dbtype(conddb.RunInfo)

		timeDiff = 0
		for run in runs:
			bestRun = session.query(RunInfo.run_number, RunInfo.start_time, RunInfo.end_time).filter(RunInfo.run_number == int(run)).first()
			if bestRun is None:
				raise Exception("Run %s can't be matched with an existing run in the database." % run)

			bestRunStartTime = calendar.timegm(bestRun[1].utctimetuple())# << 32
			bestRunStopTime  = calendar.timegm(bestRun[2].utctimetuple())# << 32

			timeDiff += (bestRunStopTime - bestRunStartTime)
		Info[i][3] = timeDiff # convert seconds into hours to avoid overflow

if sys.argv[1]=='test':
	sys.stderr.write('Estimating dataset size ...\n')
	f = open(MarkFile, 'w')
	datasets = getListOfDatasets(DATASETMASK)
	for dataset in datasets:
		extractDatasetInfo (dataset, f)
	f.close()

	sys.stderr.write('Estimating dataset duration ...\n')
	getTime()
	for info in Info:
		# datset name | number of events | dataset size | dataset duration
		print info[0], info[1], info[2], info[3] # you can pipe this to a file and manipulate output with awk
		# cat EvtSizes.txt | awk '{print $1, $3*1024/$2, $2/$4}'
	sys.stderr.write('Done!\n')

