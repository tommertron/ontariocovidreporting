## Import Modules 
from datetime import date
import json
import urllib.request as ur
import urllib.parse as prs
import pyperclip
from datetime import datetime, timedelta
startTime = datetime.now()

# Replace Spaces Function

def replacespace (item):
	item = item.replace(' ', '%20')
	return (item)

# Define Query Parameters

## URL Query Variables - Universal

urlstart = 'https://data.ontario.ca/api/3/action/datastore_search?'	
today = str(date.today())+'T00:00:00'
urlfilter = ''
fieldQuery = ''
resourceid = ''
friendlyname = '' 

## URL Query Variables - Per Dataset
resourceidlist = {
	'Vaccinedata': '8a89caa9-511c-4568-af89-7f2174b4378c',
	'Casedata': 'ed270bb8-340b-41f9-a7c6-e8ef587e6d11'
	}
datefieldlist = {
	'Vaccinedata': 'report_date',
	'Casedata': 'Reported Date'
	}
fieldlist = {
	'Vaccinedata': ['total_doses_administered', 'total_individuals_fully_vaccinated'],
	'Casedata': ['Total Cases', 'Number of patients hospitalized with COVID-19']
	}
friendlynamelist = {
	'Vaccinedata': 'Vaccine Data',
	'Casedata': 'Case Data'
	}

clipboardresult = ''

## Variable to store all results so we can compare them 

coviddataset = {
  'Total Cases': [],
  'Number of patients hospitalized with COVID-19': [],
  'total doses administered': [],
  'total individuals fully vaccinated': [],
}

resultstotal = 0

emailbody = ""

def getcoviddata(dataset,fetchdate):
	# Get dataset specific values for the query
	resourceid = resourceidlist[dataset]
	friendlyname = friendlynamelist[dataset]
	fields = fieldlist[dataset]
	urlfilter = '\"' + datefieldlist[dataset] + '\":'+ '\"' + fetchdate + '\"'
	urlfilter = urlfilter.replace(' ', '%20')
	fieldQuery = ''
	# Set global variables
	global resultstotal 
	global coviddataset
	# clipboardresult = clipboardresult
	fields = fieldlist[dataset]
	## Create field list query section
	for x in fields[:-1]:
		fieldQuery = fieldQuery+'\''+x+'\','
	fieldQuery = fieldQuery+'\''+fields[len(fields)-1]+'\''
	fieldQuery = fieldQuery.replace(' ', '%20')
	fieldQuery = fieldQuery.replace('\'', '\"')
	# Make url
	queryurl = urlstart + 'resource_id=' + resourceid + '&fields=' + fieldQuery + '&filters={' + urlfilter + '}'
	#print ('** ' + friendlynamelist[dataset] + ' Report **')
	#print ('query url was ' + queryurl) # Uncomment for troubleshooting
	url = queryurl
	fileobj = ur.urlopen(url)
	## Format Data Into Json
	gotdata = fileobj.read()
	nicedata = json.loads(gotdata)
	resultstotal = resultstotal + nicedata['result']['total']
	resultscheck = nicedata['result']['total']
	if resultscheck > 0:
		for i in nicedata['result']['records'][0]:
			recname = i
			recnum = nicedata['result']['records'][0][i]
			recname = recname.replace('_', ' ')
			if type(recnum) == str:
				recnum = recnum.replace(',', '')
			# Add result to global dataset
			coviddataset[recname].append(recnum)

## Define some dates!
getdate = date.today()
reportingdate = getdate.strftime("%B %d, %Y") # This is used to display the date the report was run

## Kick off intro / heading 
# print ('')
# print ('Tom\'s Ontario Covid Report for ' + reportingdate)
# print ('')

# Get all the data
daysback = 0 # sets how many days back from today to get data 
datasetnum = 0
while daysback < 3:
	getcoviddata ('Vaccinedata',str(getdate - timedelta(days=daysback)))
	datasetnum = datasetnum + 1
	getcoviddata ('Casedata',str(getdate - timedelta(days=daysback)))
	datasetnum = datasetnum + 1
	daysback = daysback + 1

if resultstotal == datasetnum:
	# Show today's numbers 
	print ('## Today\'s Data')
	for i in coviddataset:
		print (i.title(),':',format(int(coviddataset[i][0]),","))
		clipboardresult = clipboardresult + str(int(coviddataset[i][0])) + '	'
	clipboardresult = clipboardresult.rstrip()
	print ('')
	print ('## Today\'s Trends')
	# Show new case data
	newcasestoday = coviddataset['Total Cases'][0] - coviddataset['Total Cases'][1] 
	newcasesyesterday = coviddataset['Total Cases'][1] - coviddataset['Total Cases'][2]
	newcaseratechange = (newcasestoday / newcasesyesterday) - 1
	print ('New Cases:',newcasestoday, '(Change of', format(newcaseratechange,".1%")+')') 
	# Calculate hospitalization changes 
	hospitalchange = coviddataset['Number of patients hospitalized with COVID-19'][0] - coviddataset['Number of patients hospitalized with COVID-19'][1]
	hospitalratechange = (coviddataset['Number of patients hospitalized with COVID-19'][0] / coviddataset['Number of patients hospitalized with COVID-19'][1])-1
	print ('Hospitalization Change:',hospitalchange,'(Change of',format(hospitalratechange,".1%")+')')
	# Calculate hospitalization rates
	ontariopop = 14570000
	vaccinepercent = (int(coviddataset['total doses administered'][0]) - int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
	vaccinerate = (int(coviddataset['total doses administered'][0]) / int(coviddataset['total doses administered'][1])) - 1
	print ('% of People With at Least One Dose:',format(vaccinepercent,".1%"),'(Change of',format(vaccinerate,".1%")+')')
	# Paste results to clipboard
	forclipboard = (getdate.strftime("%m/%d") + "	" + clipboardresult)
	pyperclip.copy(forclipboard)
else:
	print ('Incomplete data for today!')

print ('')

## Show script runtime - uncomment for troubleshooting 
# print(datetime.now() - startTime)
