## Import Modules 
from datetime import date
import json
import urllib.request as ur
import urllib.parse as prs
import pyperclip #Note - you'll need to install this module as a separate package on your local machine or this will fail. 
from datetime import datetime, timedelta
import sys

scriptstart = datetime.now()

# Define Query Parameters

## URL Query Variables - Universal
### These are the variables we will use to build our query.
urlstart = 'https://data.ontario.ca/api/3/action/datastore_search?'
today = str(date.today())+'T00:00:00'
urlfilter = ''
fieldQuery = ''
resourceid = ''
friendlyname = '' 

## URL Query Variables - Per Dataset
### Each Ontario dataset has a unique resource ID that we use to identify it when querying.
resourceidlist = {
	'Vaccinedata': '8a89caa9-511c-4568-af89-7f2174b4378c',
	'Casedata': 'ed270bb8-340b-41f9-a7c6-e8ef587e6d11'
	}
### For some reason, each Ontario dataset seems to have a different field name for reported data. This specifies the correct date field name per dataset so we can query by date. 
datefieldlist = {
	'Vaccinedata': 'report_date',
	'Casedata': 'Reported Date'
	}
### This variable stores all of the fields we want to retrieve from each Ontario dataset. The script will get and print all of today's data for each field listed here.
fieldlist = {
	'Vaccinedata': ['total_doses_administered', 'total_individuals_fully_vaccinated'],
	'Casedata': ['Total Cases', 'Number of patients hospitalized with COVID-19','Number of patients in ICU due to COVID-19']
	}
## This specifies what we want to call each dataset when we output its results. 
friendlynamelist = {
	'Vaccinedata': 'Vaccine Data',
	'Casedata': 'Case Data'
	}

## Create a dictionary variable that will store the all the data that we retrieve
coviddataset = {}
## This little loop takes all of the fields we listed in 'field list' and adds them to the coviddataset dictionary variable as keys. We'l use this later to parse through and add values to.
for x, value in fieldlist.items():
	for i in value:
		i = i.replace('_',' ')
		coviddataset[i] = []

## Creates the clipboard result variable where we'll later add to for copying to the local clipboard. This is to help pasting the data onto a spreadsheet. 
clipboardresult = ''

resultstotal = 0


def getcoviddata(dataset,getdays,fetchdate):
	# Get dataset specific values for the query
	resourceid = resourceidlist[dataset]
	friendlyname = friendlynamelist[dataset]
	fields = fieldlist[dataset]
	urlfilter = '\"' + datefieldlist[dataset] + '\":'+ '['
	expectedresults = getdays
	#getdays = getdays + 1
	while getdays > 0:
		urlfilter = urlfilter + '\"' + str(fetchdate) + '\"'
		fetchdate = fetchdate - timedelta(days=1)
		getdays = getdays - 1
		if getdays > 0:
			urlfilter = urlfilter + ','
	urlfilter = urlfilter+']'
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
	#print (urlstart + 'resource_id=' + resourceid + '&fields=' + fieldQuery + '&filters={' + urlfilter + '}') # This prints what the url will be. Uncomment and paste the result into a browser to troubleshoot.
	queryurl = urlstart + 'resource_id=' + resourceid + '&fields=' + fieldQuery + '&filters={' + urlfilter + '}'
	#print ('** ' + friendlynamelist[dataset] + ' Report *')
	url = queryurl
	fileobj = ur.urlopen(url)
	## Format Data Into Json
	gotdata = fileobj.read()
	nicedata = json.loads(gotdata)
	resultstotal = resultstotal + nicedata['result']['total']
	resultscheck = nicedata['result']['total']
	if resultscheck > 0:
		quay = expectedresults -1
		while quay > 0-1:
			for i in nicedata['result']['records'][quay]:
				recname = i
				recnum = nicedata['result']['records'][quay][i]
				recname = recname.replace('_', ' ')
				if type(recnum) == str:
					recnum = recnum.replace(',', '')
				# Add result to global dataset
				coviddataset[recname].append(recnum)
			quay = quay -1

## Define some dates!
reporteddate = ''

askeddate = 'today' if len(sys.argv) == 1 else sys.argv[1]
if askeddate == 'yesterday':
	getdate = date.today() - timedelta(days=1)
	reporteddate = '**Yesterday\'s Data**',getdate
else:
	getdate = date.today()

reportingdate = getdate.strftime("%B %d, %Y") # This is used to display the date the report was run

# Get all the data
daysget = 9 # sets how many days of data to get (starting from today)

getcoviddata ('Vaccinedata',daysget,getdate)
getcoviddata ('Casedata',daysget,getdate)

## This part of the script takes the data, does some calculations, and returns the results.
if resultstotal == daysget *2:
	# Show today's numbers 
	for i in coviddataset:
		# print ('-',i.title(),':',format(int(coviddataset[i][0]),","))
		clipboardresult = clipboardresult + str(int(coviddataset[i][0])) + '	'
	clipboardresult = clipboardresult.rstrip()
	# Calculate and display new cases
	print ('## 🦠 Case Data')
	newcasestoday = coviddataset['Total Cases'][0] - coviddataset['Total Cases'][1] 
	newcasesyesterday = coviddataset['Total Cases'][1] - coviddataset['Total Cases'][2]
	newcaseratechange = (newcasestoday / newcasesyesterday) - 1
	if newcaseratechange < 0:
		arrow = '⬇️'
		newcaseratechange = newcaseratechange * -1
	else:
		arrow = '⬆️'
	print ('- New Cases:',str(round(newcasestoday)), '('+arrow,format(newcaseratechange,".1%")+')') 
	# Calculate and display 7 day average 
	def sevavcalc(startday):
		if startday == 'today':
			x = 0
			y = 7
		else: 
			x = 1
			y = 8
		sevendaynewcases = [] 
		while x < y:
			sevendaynewcases.append(coviddataset['Total Cases'][x] - coviddataset['Total Cases'][x+1])
			x += 1
		return (sum(sevendaynewcases) / 7)
	sevdayratechange = sevavcalc('today') / sevavcalc('yesterday') -1
	if sevdayratechange > 0:
		arrow = '⬆️'
	else: 
		arrow = '⬇️' 
	print ('- 7 Day Average New Case count:',round(sevavcalc('today')),'('+arrow,format(sevdayratechange,".1%")+')')
	# 🏥 Hospitalization Data
	print ('## 🏥 Hospitalization Data')
	def ratechange (datum):
		change = round(coviddataset[datum][0] - coviddataset[datum][1])
		ratechange = (coviddataset[datum][0] / coviddataset[datum][1])-1
		if ratechange < 0:
			arrow = '⬇️'
			ratechange = ratechange * -1
			color = 'green'
		else:
			arrow = '⬆️'
			color = 'red'
		return ('<span style="color:'+color+'\">'+str(change)+'</span>'+' ('+arrow+" "+str(format(ratechange,".1%"))+')')
	print ('- Number of patients in hospital:',coviddataset['Number of patients hospitalized with COVID-19'][0])
	print ('- Hospitalization Change:',str(ratechange('Number of patients hospitalized with COVID-19')))
	print ('- Number of patients in ICU:',coviddataset['Number of patients in ICU due to COVID-19'][0])
	print ('- ICU Change:',str(ratechange('Number of patients in ICU due to COVID-19')))
	# Calculate and display vaccination rates
	print ('## 💉 Vaccination Data')
	ontariopop = 14711800
	def vaxchange (datum):
		vaccinepercent = (int(coviddataset[datum][0]) - int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
		vaccinerate = (int(coviddataset[datum][0]) / int(coviddataset[datum][1])) - 1
		if vaccinerate < 0:
			arrow = '⬇️'
			vaccinerate = vaccinerate * -1
		else:
			arrow = '⬆️'
		return (str(format(vaccinepercent,".1%"))+' ('+arrow+" "+str(format(vaccinerate,".1%"))+')')
	print ('- % of People With at Least One Dose:',vaxchange('total doses administered'))
	vaccinepercent = (int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
	vaccinerate = (int(coviddataset['total individuals fully vaccinated'][0]) / int(coviddataset['total individuals fully vaccinated'][1])) - 1
	if vaccinerate < 0:
		arrow = '⬇️'
		vaccinerate = vaccinerate * -1
	else:
		arrow = '⬆️'
	print ('- % of People Fully Vaccinated:',format(vaccinepercent,".1%"),'('+arrow,format(vaccinerate,".2%")+')')
	# Paste results to clipboard
	forclipboard = (getdate.strftime("%m/%d") + "	" + clipboardresult)
	pyperclip.copy(forclipboard)
else:
	print ('Incomplete data for today!\n')
	coviddataset = {
	  'Total Cases': [],
	  'Number of patients hospitalized with COVID-19': [],
	  'total doses administered': [],
	  'total individuals fully vaccinated': [],
	}
	getcoviddata ('Vaccinedata',daysget,getdate)
	getcoviddata ('Casedata',daysget,getdate)
	for i in coviddataset:
		print ('- ',i,":",coviddataset[i])

# This prints the reported date if yesterday was asked for.
if reporteddate != '':
	print (reporteddate)

# Show script runtime - uncomment for troubleshooting 
# print (datetime.now() - scriptstart)
