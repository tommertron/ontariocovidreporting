## Import Modules 
from datetime import date
import json
import urllib.request as ur
import urllib.parse as prs
from datetime import datetime, timedelta
import sys
from sys import platform
import requests

def logIt (event):
	now = datetime.now()
	logDateTime = now.strftime("%m/%d/%y - %H:%M:%S.%f")[:-5]
	f = open('log.txt','a')
	f.write('\n'+logDateTime+" - "+event)
	f.close()

# Sets some variables based on arguments that were passed in. 
cron = ''

if len(sys.argv) > 1:
	argslot = 1
	for i in sys.argv[1:]:
		if sys.argv[argslot] == 'yesterday':
			getdate = date.today() - timedelta(days=1)
			reporteddate = '**Yesterday\'s Data**',getdate
		elif sys.argv[argslot] == 'cron':
			cron = '(CRON)'
		argslot += 1

logIt ("Starting script"+cron)

# Create html stuff 
htmlstart = '<span style="color:'
htmlend = '</span>'

## Define some dates!
reporteddate = ''
getdate = date.today()# + timedelta(days=+1) #Uncomment the right section to point to tomorrow's date. To test instances where today's data is not available.
formattedToday = str(getdate.strftime('%m/%d'))

def checkfile(file_name, string_to_search):
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            if string_to_search in line:
                return True
    return False

reportingdate = getdate.strftime("%B %d, %Y") # This is used to display the date the report was run

## Tokens
def keygetter(file):
	 f = open(file,'r')
	 return f.read()

BDToken = keygetter('BDToken.txt')
IFToken = keygetter('IFToken.txt')

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
for x in fieldlist:
	for i in fieldlist[x]:
		i = i.replace('_',' ')
		coviddataset[i] = []

resultstotal = 0

# Create variables for email to be sent out 
esubject = 'Tom\'s Ontario COVID Report for '+str(getdate.strftime('%B %d, %Y'))
emailbody = ''

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
	queryurl = urlstart + 'resource_id=' + resourceid + '&fields=' + fieldQuery + '&filters={' + urlfilter + '}' + '&sort=\"' + datefieldlist[dataset] + '\"'
	queryurl = queryurl.replace(' ', '%20')
	#print (queryurl)
	#print ('** ' + friendlynamelist[dataset] + ' Report *')
	url = queryurl
	fileobj = ur.urlopen(url)
	## Format Data Into Json
	gotdata = fileobj.read()
	nicedata = json.loads(gotdata)
	resultstotal = resultstotal + nicedata['result']['total']
	resultscheck = nicedata['result']['total']
	if resultscheck > 0:
		quay = resultscheck -1
		while quay > 0-1:
			for i in nicedata['result']['records'][quay]:
				recname = i
				recnum = nicedata['result']['records'][quay][i]
				recname = recname.replace('_', ' ')
				if type(recnum) == str:
					recnum = recnum.replace(',', '')
				# Add result to global dataset
				coviddataset[recname].append(recnum)
			quay = quay - 1

# Sets the parameters to determine the emoji to use based on how many arrows are pointing up. 
howrthings = {"0":"🥳","1":"🙂","2":"😕","3":"😔","4":"😨","5":"😱"}
gauge = 0

# Run the function to get coviddata for vaccines and cases.
daysget = 9 # sets how many days of data to get (starting from today)

if checkfile ('dates.txt',formattedToday) == False:
	getcoviddata ('Vaccinedata',daysget,getdate)
	getcoviddata ('Casedata',daysget,getdate)
else:
	print ('Email already sent; did not check for data')
	logIt ('Email already sent; did not check for data')

def adddata (string, kind):
	push = string
	if kind == 'bullet':
		mdstrt = '-'
		htmlstart = '<li>'
		htmlend = '</li>'
	elif kind == 'heading':
		mdstrt = '#'
		htmlstart = '<h1>'
		htmlend = '</h1>'
	elif kind == 'whitespace':
		mdstrt = ''
		htmlstart = '<br>'
		htmlend = ''
	elif kind == 'p':
		mdstrt = ''
		htmlstart = '<p>'
		htmlend = '</p>'
	print (mdstrt,push)
	global emailbody
	emailbody = emailbody + htmlstart + push + htmlend

# Function to get a seven day average for a given dataset 
def sevavcalc(startday,datum):
	if startday == 'today':
		x = 0
		y = 7
	else: 
		x = 1
		y = 8
	sevendays = [] 
	while x < y:
		sevendays.append(int(datum[x]) - int(datum[x+1]))
		x += 1
	return (sum(sevendays) / 7)

## This part of the script takes the data, does some calculations, and returns the results.
if checkfile ('dates.txt',formattedToday) == False:
	print ('Looks like email was not sent')
	if resultstotal == daysget *2:
		#----------- Format data, print it, log it to gsheet and send email -----------  
		
		#----------- Case Data -----------  
		adddata ('🦠 Case Data','heading')
		newcasestoday = coviddataset['Total Cases'][0] - coviddataset['Total Cases'][1] 
		newcasesyesterday = coviddataset['Total Cases'][1] - coviddataset['Total Cases'][2]
		newcaseratechange = (newcasestoday / newcasesyesterday) - 1
		if newcaseratechange < 0:
			arrow = '⬇️'
			newcaseratechange = newcaseratechange * -1
		else:
			arrow = '⬆️'
			gauge += 1
		adddata ('New Cases: '+str(round(newcasestoday))+' ('+arrow+' '+str(format(newcaseratechange,".1%"))+')','bullet') 
		# Calculate and display 7 day average 
		sevdayratechange = sevavcalc('today',coviddataset['Total Cases']) / sevavcalc('yesterday',coviddataset['Total Cases']) -1
		if sevdayratechange > 0:
			arrow = '⬆️'
			gauge += 1
		else: 
			arrow = '⬇️' 
		adddata ('7 Day Average New Case count: '+str(round(sevavcalc('today',coviddataset['Total Cases'])))+' ('+arrow+' '+str(format(sevdayratechange,".1%"))+')','bullet')

		# ----------- Hospitalization Data -----------   
		adddata('🏥 Hospitalization Data','heading')
		def ratechange (datum):
			change = round(coviddataset[datum][0] - coviddataset[datum][1])
			ratechange = (coviddataset[datum][0] / coviddataset[datum][1])-1
			global gauge
			if ratechange < 0:
				arrow = '⬇️'
				ratechange = ratechange * -1
				color = 'green\">'
			else:
				arrow = '⬆️'
				gauge += 1
				color = 'red\">'
			return (htmlstart+color+str(change)+htmlend+' ('+arrow+" "+str(format(ratechange,".1%"))+')')
		adddata ('Number of patients in hospital: '+str(coviddataset['Number of patients hospitalized with COVID-19'][0]),'bullet')
		adddata ('Hospitalization Change: '+str(ratechange('Number of patients hospitalized with COVID-19')),'bullet')
		adddata ('Number of patients in ICU: '+str(coviddataset['Number of patients in ICU due to COVID-19'][0]),'bullet')
		adddata ('ICU Change: '+str(ratechange('Number of patients in ICU due to COVID-19')),'bullet')
	
		# ----------- Vaccine Data -----------  
		adddata ('💉 Vaccination Data','heading')
		ontariopop = 14755211
		def vaxchange (datum):
			vaccinepercent = (int(coviddataset[datum][0]) - int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
			vaccinerate = (int(coviddataset[datum][0]) / int(coviddataset[datum][1])) - 1
			if vaccinerate < 0:
				arrow = '⬇️'
				vaccinerate = vaccinerate * -1
			else:
				arrow = '⬆️'
			return (str(format(vaccinepercent,".1%"))+' ('+arrow+" "+str(format(vaccinerate,".1%"))+')')
		adddata ('% of People With at Least One Dose: '+str(vaxchange('total doses administered')),'bullet')
		vaccinepercent = (int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
		vaccinerate = (int(coviddataset['total individuals fully vaccinated'][0]) / int(coviddataset['total individuals fully vaccinated'][1])) - 1
		if vaccinerate < 0:
			arrow = '⬇️'
			vaccinerate = vaccinerate * -1
		else:
			arrow = '⬆️'
		adddata ('% of People Maxxinated: '+str(format(vaccinepercent,".1%"))+' ('+arrow+' '+str(format(vaccinerate,".2%"))+')','bullet')
		sevdayratechange = sevavcalc('today',coviddataset['total doses administered']) / sevavcalc('yesterday',coviddataset['total doses administered']) -1
		if sevdayratechange > 0:
			arrow = '⬆️'
		else: 
			arrow = '⬇️'
			gauge += 1
		sevdaydoseav = f"{sevavcalc('today',coviddataset['total doses administered']):,.0f}"
		adddata ('7 Day Average Doses Administered: '+ sevdaydoseav +' ('+arrow+' '+str(format(sevdayratechange,".1%"))+')','bullet')
		adddata ('Overall, how are things going right now?','heading')
		adddata (howrthings[str(gauge)],'heading')
		esubject = esubject + ': ' + howrthings[str(gauge)]
		adddata ('Doug Ford Must Resign','p')
		emailbody = emailbody + '<p>If you find this report useful, please consider making a <a href="https://secure3.convio.net/dbfb/site/SPageNavigator/Donation_Forms/donation_splash_page.htm">donation</a> to the Daily Bread Food Bank.</p>'
	
		# Send results to the gsheet and send email unless already done

		if platform == 'linux':
			if checkfile ('dates.txt',formattedToday) == False:
				f = open('dates.txt','a')
				f.write('\n'+formattedToday)
				f.close()
				hookurl = 'https://maker.ifttt.com/trigger/addsheet/with/key/'+IFToken
				payload = {
					"value1":str(coviddataset['total doses administered'][0])+'|'+str(coviddataset['total individuals fully vaccinated'][0]),"value2":str(coviddataset['Total Cases'][0])+'|'+str(coviddataset['Number of patients hospitalized with COVID-19'][0]),"value3":str(coviddataset['Number of patients in ICU due to COVID-19'][0])+'|'+str(getdate)}
				headers = {}
				res = requests.post(hookurl, data=payload, headers=headers)
				url = "https://api.buttondown.email/v1/emails"
				payload = {
					"body": emailbody,
					"subject": esubject
					}
				headers = {
					"Authorization": f"TOKEN {'BDToken'}"
				}
				res = requests.post(url, data=payload, headers=headers)
				logIt ("Email sent with complete data.")
			else:
				logIt ("Complete data, but email already sent.")
		else: logIt ("Complete data, but not running in production, so no email sent.")
	else:
		print ('Incomplete data for today!\n')
		logIt ("Incomplete data for today!")
# 	coviddataset = {
# 	  'Total Cases': [],
# 	  'Number of patients hospitalized with COVID-19': [],
# 	  'Number of patients in ICU due to COVID-19': [],
# 	  'total doses administered': [],
# 	  'total individuals fully vaccinated': [],
# 	}
# 	getcoviddata ('Vaccinedata',daysget,getdate)
# 	getcoviddata ('Casedata',daysget,getdate)
# 	for i in coviddataset:
# 		print ('- ',i,":",coviddataset[i])

# This prints the reported date if yesterday was asked for.
if reporteddate != '':
	print (reporteddate)

logIt ("Script Complete"+cron+"\n")

# Show script runtime - uncomment for troubleshooting 

#print ('\nTimet to run: ',datetime.now() - scriptstart)
