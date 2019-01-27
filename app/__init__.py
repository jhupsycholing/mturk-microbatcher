# Author: Brian Leonard
# Organization: JHU Computational Psycholinguistics Lab
# Email: bleona10@jhu.edu





from flask import Flask, redirect, request, send_from_directory, render_template, jsonify, Response
import boto3
import sqlite3
import os
from flask import g
import sys
import random
from datetime import datetime
from dateutil.tz import tzlocal
import calendar
from apscheduler.schedulers.background import BackgroundScheduler
import time
from flask_sqlalchemy import SQLAlchemy
import ast
from flask_cors import CORS, cross_origin
import xml.etree.ElementTree as ET
import json
from flask_cachebuster import CacheBuster

#start flask app, specify static url directory
app = Flask(__name__,static_url_path='/static')

#enable cross-origin requests
CORS(app,support_credentials=True,resources={r"/api/*":{'origins':'*'}})

#load config variables
app.config.from_pyfile('appconfig.cfg')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

#make sure js and css reload after every update
cache_buster = CacheBuster(config={'extensions':['.js','.css'],'hash_size':10})
cache_buster.init_app(app)


#grab db using app config specifications
db = SQLAlchemy(app)

#check config if in sandbox
if app.config['SANDBOX']:
	debug = True
else:
	debug = False

#db specifications
from models import submit,HIT



# ----------------------------------------------------------------

#Load HIT Creation Page
@app.route('/createHIT')

def createHit():
	dbHITs = HIT.query.all()
	dbHITs = [hit for hit in dbHITs if hit.HITId == hit.HITGroup]

	HITinfo = []

	for hit in dbHITs:
		HITinfo += [{'HITId':hit.HITId,'Title':hit.title,'Created':hit.created}]

	return render_template('createHIT.html', qualifications=getQualifications(),HITs=HITinfo)

# ----------------------------------------------------------------
# Get info from previous HIT to populate HIT creation form
@app.route('/getHITInfo')

def getHITInfo():
	HITId = request.args.get('HITId')
	HITinfo = client.get_hit(HITId=HITId)['HIT']
	dbHIT = HIT.query.filter_by(HITId=HITId).first()
	HITinfo['ibexURL'] = dbHIT.ibexURL
	HITinfo['Timeout'] = dbHIT.timeout / 60
	HITinfo['Reward'] = float(HITinfo['Reward'])
	HITinfo['Excluded'] = []
	HITinfo['Included'] = []
	HITinfo['surveyCode'] = dbHIT.surveyCode
	HITinfo['Duration'] = (HITinfo['Expiration'] - HITinfo['CreationTime']).days
	if HITinfo['Duration'] < 2: HITinfo['Duration'] = 2

	if debug:
		masters_id = '2ARFPLSP75KLA8M8DH1HTEQVJT3SY6'
	else:
		masters_id = '2F1QJWKUDD8XADTFD2Q0G6UTO95ALH'

	location_id = '00000000000000000071'

	for qual in HITinfo['QualificationRequirements']:
		if qual['QualificationTypeId'] == masters_id:
			if qual['Comparator'] == 'Exists':
				HITinfo['Masters'] = True
			else:
				HITinfo['Masters'] = False
		if qual['QualificationTypeId'] == location_id and qual['Comparator'] == 'EqualTo' and qual['LocaleValues']['Country'] == 'US':
			HITinfo['US'] = True
		else:
			HITinfo['US'] = False
		if qual['QualificationTypeId'] == '00000000000000000040':
			HITinfo['NumberApproved'] = qual['IntegerValues'][0]
		if qual['QualificationTypeId'] not in [masters_id,location_id,'00000000000000000040']:
			if qual['Comparator'] == 'DoesNotExist':
				HITinfo['Excluded'].append(qual['QualificationTypeId'])
			if qual['Comparator'] == 'Exists':
				HITinfo['Included'].append(qual['QualificationTypeId'])

	return jsonify(HITinfo)

# ----------------------------------------------------------------

#Distribute one HIT of a given list
@app.route('/ibex')

def ibex():
	#get assignment info
	workerId = request.args.get('workerId')
	assignmentId = request.args.get('assignmentId')
	HITId = request.args.get('HITId')

	#get hit info from db
	hit = HIT.query.filter_by(HITId=HITId).first()
	ibexURL = hit.ibexURL
	lists = ast.literal_eval(hit.lists)
	lists_distributed = ast.literal_eval(hit.lists_distributed)
	lists_completed = ast.literal_eval(hit.lists_completed)

	#check if this user was already assigned a list -- in case they accidentally close and reopen the submission link
	submitted_assignments = submit.query.filter_by(hit=HITId).all()
	for ass in submitted_assignments:
		if assignmentId == ass.assignment and workerId == ass.worker:
			#we inform subjects in our ibex experiments beforehand that they will not be allowed to use the survey link twice, to discourage them from restarting the experiment
			return "As indicated in the instructions, this link only works once. For the validity of our experimental results, we request that turkers only go through the experiment once. Please return the HIT."
			#if we're okay with the survey link working multiple times, we return the subject to the same list they began with
			#return(redirect(ibexURL + '?withsquare' + str(ass.list)))

	#determine the remaining unassigned and uncompleted lists
	for listnum in lists_distributed:
		lists.remove(listnum)
	for listnum in lists_completed:
		lists.remove(listnum)

	#normal case -- if there are lists that have yet to be distributed or completed, use one of them
	if len(lists) != 0:
		#pick a list at random and add it to the record of lists we have distributed
		whichlist = random.choice(lists)
		lists_distributed.append(whichlist)
		hit.lists_distributed = str(lists_distributed)
		db.session.commit()
	#special condition -- if every list has been either distributed or completed, and a request is being made, 
	#that means that one of the distributed lists has timed out, so we should select from those options.
	else:
		whichlist = random.choice(lists_distributed)

	#keep track of the number of times a turker accepts the hit and uses the survey link. compare to final results to assess worker dropout rates.
	hit.numGrabbed += 1
	db.session.commit()



	#Add record for this assignment to the database
	submission = submit(assignment=assignmentId,hit=HITId,list=whichlist,worker=workerId,submitted=0)
	db.session.add(submission)
	db.session.commit()

	#if this is an ibex experiment, redirect to ibex with the assigned list
	if 'ibex' in ibexURL:
		return(redirect(ibexURL + '?withsquare=' + str(whichlist)))
	#if using a custom application, use the /experiment address to load your app
	else:
		return(redirect('/experiment?list='+str(whichlist)+'&assignmentId='+assignmentId+'&HITId='+HITId+'&workerId='+workerId))
		#return experiment(list=str(whichlist),assignmentId=assignmentId,HITId=HITId,workerId=workerId)

# ----------------------------------------------------------------
#Handle the submission of a HIT. This function is called when the attempts to input a survey code
@app.route('/submit')

def submitAssignment():
	#get info
	assignmentId = request.args.get('assignmentId')
	hitId = request.args.get('hitId')
	code = request.args.get('code')

	#grab database records
	hit = HIT.query.filter_by(HITId=hitId).first()
	submission = submit.query.filter_by(assignment=assignmentId).first()
	

	#if the subject has not actually started the experiment
	if submission == None:
		print 'no submit'
		return jsonify(valid='nosub')

	worker = submission.worker

	#if this turker's code has already been verified
	if submission.submitted == 1:
		print 'already submitted'
		return jsonify(valid='true')

	#check if submitted survey code is correct
	#else, return client to previous page
	if code.lower() == hit.surveyCode.lower():
		#indicate this user has successfully submitted their code
		submission.submitted = 1
		db.session.commit()
		#remove the list for this assignment from the lists distributed and add it to lists completed
		lists_distributed = ast.literal_eval(hit.lists_distributed)
		lists_completed = ast.literal_eval(hit.lists_completed)
		lists_distributed.remove(submission.list)
		lists_completed.append(submission.list)
		hit.lists_distributed = str(lists_distributed)
		db.session.commit()
		hit.lists_completed = str(lists_completed)
		db.session.commit()

		#get the remaining distributed and incomplete hits
		new_lists = ast.literal_eval(hit.lists)
		for li in lists_completed:
			new_lists.remove(li)

		#if all current assignments have been submitted
		if len(lists_completed) == hit.batch:

			remaining = len(new_lists)

			#make sure to release 9 or less subjects at a given time, to avoid mturk doubling the surcharge
			if remaining > 9:
				remaining = 9

			#number of subjects for the next batch
			newbatch = remaining

			#if collection is not complete
			if newbatch != 0:
				#get hit info
				get_hit = client.get_hit(HITId=hit.HITGroup)

				#create new identical subhit
				response = client.create_hit(
					MaxAssignments=newbatch,
					LifetimeInSeconds=2*24*60*60, #convert to seconds
					AssignmentDurationInSeconds=get_hit['HIT']['AssignmentDurationInSeconds'],
					Reward = get_hit['HIT']['Reward'],
					Title=get_hit['HIT']['Title'],
					Description=get_hit['HIT']['Description'],
					Keywords = get_hit['HIT']['Keywords'],
					Question = get_hit['HIT']['Question'],
					QualificationRequirements=get_hit['HIT']['QualificationRequirements'])

				#add record for new sub-HIT. Each group of sub-HITs is identified by the HITGroupId, which is the HITId of the first sub-HIT
				newHIT = HIT(HITId=response['HIT']['HITId'],title=hit.title,lists=str(new_lists),lists_distributed='[]',lists_completed='[]',batch = newbatch,timeout=hit.timeout,ibexURL=hit.ibexURL,maxNum=hit.maxNum,surveyCode=hit.surveyCode,numGrabbed=0,HITGroup = hit.HITGroup)
				db.session.add(newHIT)
				db.session.commit()

		

		#get qualifications
		quals = getQualifications()

		#don't use qualifications in sandbox
		if not debug:
			for qual in quals:
				#associate worker with qualification indicating they have completed an experiment with this title
				if qual['name'] == hit.title:

					response = client.associate_qualification_with_worker(
						QualificationTypeId=qual['QualID'],
						WorkerId = worker,
						IntegerValue=0,
						SendNotification=False)
				#associate worker with qualification indicating they have completing a HIT within this HITGroup (group of micro-batches)
				if hit.HITGroup in qual['name']:
					response = client.associate_qualification_with_worker(
						QualificationTypeId=qual['QualID'],
						WorkerId = worker,
						IntegerValue=0,
						SendNotification=False)


		#validate submission
		response = jsonify(valid='true')
		return response
	else:
		#if code is incorrect, do not validate
		response = jsonify(valid='false')
		return response



# ----------------------------------------------------------------
# Handle submit call from external question (internal web-app)

@app.route('/externalSubmit')

#This function is useful if you have a custom web experiment 
#At the end of your experiment, you should use javascript to submit the form with the necessary variables to the mturk 
#external submit URL. This form should include the assignmentId and whatever results you collected in the experiment

def externalSubmit():
	#basic info to keep track of through ajax
	assignmentId = request.args.get('assignmentId')
	hitId = request.args.get('HITId')

	#grab the relevant HIT
	hit = HIT.query.filter_by(HITId=hitId).first()
	#grab the assignment
	submission = submit.query.filter_by(assignment=assignmentId).first()

	#remove the list for this assignment from the record of distributed lists and add it to the list of completed lists
	lists_distributed = ast.literal_eval(hit.lists_distributed)
	lists_completed = ast.literal_eval(hit.lists_completed)
	lists_distributed.remove(submission.list)
	lists_completed.append(submission.list)
	hit.lists_distributed = str(lists_distributed)
	db.session.commit()
	hit.lists_completed = str(lists_completed)
	db.session.commit()

	#get record of undistributed and incomplete hits
	new_lists = ast.literal_eval(hit.lists)
	for li in lists_completed:
		new_lists.remove(li)

	#if all current assignments have been submitted
	if len(lists_completed) == hit.batch:

		#how many more subjects are required
		remaining = len(new_lists)
		#make sure to do a maximum of 9 subjects at a time, or amazon will double their surcharge
		if remaining > 9:
			remaining = 9

		#get size of new batch
		newbatch = remaining

		#if collection is not complete
		if newbatch != 0:
			#grab hit info from database
			get_hit = client.get_hit(HITId=hit.HITGroup)

			#create a new, identical HIT with 9 or less subjects
			response = client.create_hit(
				MaxAssignments=newbatch,
				LifetimeInSeconds=2*24*60*60, #convert to seconds
				AssignmentDurationInSeconds=get_hit['HIT']['AssignmentDurationInSeconds'],
				Reward = get_hit['HIT']['Reward'],
				Title=get_hit['HIT']['Title'] ,
				Description=get_hit['HIT']['Description'],
				Keywords = get_hit['HIT']['Keywords'],
				Question = get_hit['HIT']['Question'],
				QualificationRequirements=get_hit['HIT']['QualificationRequirements'])

			#make a db entry for new HIT. It is connected to all other sub-HITs in this group by the HITGroup variable, which is the HITId of the first sub-HIT from this group
			newHIT = HIT(HITId=response['HIT']['HITId'],title=hit.title,lists=str(new_lists),lists_distributed='[]',lists_completed='[]',batch = newbatch,timeout=hit.timeout,ibexURL=hit.ibexURL,maxNum=hit.maxNum,surveyCode=hit.surveyCode,numGrabbed=0,HITGroup = hit.HITGroup)
			db.session.add(newHIT)
			db.session.commit()

	#get qualifications
	quals = getQualifications()

	#using qualifications is an unecessary hassle in sandbox mode
	if not debug:
		for qual in quals:
			#this qualification is identified by the HIT's title and keeps track of which workers have completed the experiment with that title
			if qual['name'] == hit.title:

				response = client.associate_qualification_with_worker(
					QualificationTypeId=qual['QualID'],
					WorkerId = submission.worker,
					IntegerValue=0,
					SendNotification=False)

	return '200 OK'
# ----------------------------------------------------------------


#Create new instance of HIT
@app.route('/create')

def create():
	#Check user password before creating HIT
	password = request.args.get('password')
	if password != app.config['PASSWORD']:
		return 'The password you entered did not match the one in your config file'


	#Collect Information from Hit Creation Form
	Title = request.args.get('Title')
	Description =request.args.get('Description')
	Keywords = request.args.get('Keywords')
	Timeout = request.args.get('Timeout')
	Duration = request.args.get('Duration')
	Reward = request.args.get('Reward')
	listNum = request.args.get('listNum')
	Ibex = request.args.get('Ibex').replace('experiment.html','server.py')
	surveyCode = request.args.get('surveyCode')
	Masters = request.args.get('Masters')
	Location = request.args.get('Location')
	Excluded = request.args.getlist('Excluded')
	Included = request.args.getlist('Included')
	allEqual = request.args.get('allequal')
	numberApproved = request.args.get('Approved')


	#Generate pool of lists to give out
	lists = []
	if allEqual == 'y':
		perList = request.args.get('perList')
		for x in range(int(listNum)):
			for _ in range(int(perList)):
				lists.append(x)
	#user requests specific quantities for each list
	else:
		for x in range(int(listNum)):
			perList = request.args.get('list'+str(x))
			for _ in range(int(perList)):
				lists.append(x)

	random.shuffle(lists)


	total = len(lists)
	#0 lists not possible
	if total == 0:
		return 'Your request could not be processed. A HIT with 0 participants cannot be submitted.'
	#if 9 or less, put up half in first batch to make sure hits are distributed correctly
	if total == 1:
		firstbatch = 1
	if total <= 9:
		firstbatch = total / 2
	else:
		firstbatch = 9


	#Specify qualifications -- modify this directly to implement Qualifications not available through the form
	qualificationRequirements = []

	if debug:
		masters_id = '2ARFPLSP75KLA8M8DH1HTEQVJT3SY6'
	else:
		masters_id = '2F1QJWKUDD8XADTFD2Q0G6UTO95ALH'

	#if requested, add masters qualification
	if Masters == 'y':
		qualificationRequirements.append({
				'QualificationTypeId':masters_id,
				'Comparator':'Exists',
				'ActionsGuarded':'DiscoverPreviewAndAccept'
			})
	else:
		qualificationRequirements.append({
				'QualificationTypeId':masters_id,
				'Comparator':'DoesNotExist',
				'ActionsGuarded':'DiscoverPreviewAndAccept'
			})

	#add qualification to ensure turker has US address
	if Location == 'y':
		qualificationRequirements.append({
				'QualificationTypeId':'00000000000000000071',
				'Comparator':'EqualTo',
				'LocaleValues': [
					{
						'Country':'US'
					}
				],
				'ActionsGuarded':'DiscoverPreviewAndAccept'
			})

	if numberApproved != '':
		numberApproved = int(numberApproved)
		qualificationRequirements.append({
				'QualificationTypeId':'00000000000000000040',
				'Comparator':'GreaterThanOrEqualTo',
				'IntegerValues':[numberApproved],
				'ActionsGuarded':'DiscoverPreviewAndAccept'
			})

	#get any qualifications associated with the title of this HIT
	quals = getQualifications()
	qual_names = [qual['name'].lower() for qual in quals]


	#if no qualification has been created yet for this Title
	if Title.lower() not in qual_names:
		create_response = client.create_qualification_type(
			Name=Title,
			Description='Completed the study named '+Title,
			QualificationTypeStatus='Active')	

		#Excluded.append(create_response['QualificationType']['QualificationTypeId'])
	#else:
		#qual_ids = [qual['QualID'] for qual in quals if qual['name'].lower() == Title.lower()]
		#for qual_id in qual_ids:
			#Excluded.append(qual_id)





	if Excluded:
		for qual in Excluded:
			qualificationRequirements.append({
					'QualificationTypeId':qual,
					'Comparator':'DoesNotExist',
					'ActionsGuarded':'DiscoverPreviewAndAccept'
				})
	if Included:
		for qual in Included:
			qualificationRequirements.append({
					'QualificationTypeId':qual,
					'Comparator':'Exists',
					'ActionsGuarded':'DiscoverPreviewAndAccept'
				})



	#if using an ibex experiment
	if 'ibex' in Ibex:

		#External Question redirects to the survey code page.
		ExternalQuestion = '''
		<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
		  <ExternalURL>https://'''+app.config['APP_NAME']+'''.herokuapp.com/surveyCodePage?timeout='''+Timeout+'''</ExternalURL>
		  <FrameHeight>800</FrameHeight>
		</ExternalQuestion>'''

		response = client.create_hit(
			MaxAssignments=firstbatch,
			LifetimeInSeconds=int(Duration)*24*60*60,
			AssignmentDurationInSeconds=int(Timeout) * 60,
			Reward = str(Reward),
			Title= Title,
			Description=Description,
			Keywords=Keywords,
			Question = ExternalQuestion,
			QualificationRequirements= qualificationRequirements
			)
	

	#if using a custom web app
	else:

		ExternalQuestion = '''
		<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
		  <ExternalURL>https://'''+app.config['APP_NAME']+'''.herokuapp.com/myCustomApp</ExternalURL>
		  <FrameHeight>800</FrameHeight>
		</ExternalQuestion>'''

		response = client.create_hit(
			MaxAssignments=firstbatch,
			LifetimeInSeconds=int(Duration)*24*60*60,
			AssignmentDurationInSeconds=int(Timeout) * 60,
			Reward = str(Reward),
			Title=Title,
			Description=Description,
			Keywords = Keywords,
			Question = ExternalQuestion,
			QualificationRequirements=qualificationRequirements)

	#This is a special qualification to make sure that there are no repeat subjects in a group of micro-batches
	create_response = client.create_qualification_type(
		Name=Title + ' -- ' + response['HIT']['HITId'],
		Description='Qualification for HITGroup',
		QualificationTypeStatus='Active')

	Excluded.append(create_response['QualificationType']['QualificationTypeId'])
	

	newHIT = HIT(HITId=response['HIT']['HITId'],title=Title,lists=str(lists),lists_distributed='[]',lists_completed='[]',batch = firstbatch,timeout=int(Timeout) * 60,ibexURL=Ibex,maxNum=total,surveyCode=surveyCode,numGrabbed=0,HITGroup = response['HIT']['HITId'],created=datetime.now())
	db.session.add(newHIT)
	db.session.commit()
	return 'HIT created!'

# ----------------------------------------------------------------
#render the survey link/code html
@app.route('/surveyCodePage')

def surveyCodePage():
	timeout = request.args.get('timeout')

	#Specify descriptive text. Customize this
	previewText = "In this HIT, you will be redirected to another website to participate in a behavioral experiment. When you have completed the experiment, you will receive a unique survey code, which you can enter below to confirm your assignment. In the experiment, you will be presented with text to read, and you may be asked simple questions about what you read. The maximum duration of this experiment is %d minutes, which is more than enough time to complete it. Once this time limit is exceeded, you will no longer be able to submit the HIT for compensation." % (int(timeout))

	#Request that all subjects be native English speakers
	nativeEnglish = True

	return(render_template('surveyLinkPage.html',previewText=previewText,nativeEnglish=nativeEnglish))


# ----------------------------------------------------------------
# Use this function to load up the html for your custom app
# This first page could constitute a consent form/instructions page
@app.route('/myCustomApp')

def textEntry():
	return 'render HTML for your custom app if you have placed it in the templates directory'
	#return render_template('customAppIndex.html')


# ----------------------------------------------------------------

#display info about HITs in the database
@app.route('/reviewHITs')

def reviewHITs():
	HITs = client.list_hits()['HITs']
	HIT_list = []

	#accumulate the statistics for every HIT in a given HITGroup
	for hit in HITs:
		db_hit = HIT.query.filter_by(HITGroup=hit['HITId']).all()

		if db_hit:
			workers = []


			this = {}
			this['title'] = hit['Title']
			this['HITId'] = hit['HITId']
			this['status'] = hit['HITStatus']
			this['available'] = 0
			this['pending'] = 0
			this['max'] = 0
			lists_completed = []
			for h in db_hit:
				this_hit = client.get_hit(HITId=h.HITId)['HIT']
				asses = client.list_assignments_for_hit(HITId=h.HITId)['Assignments']
				workers += [ass['WorkerId'] for ass in asses]

				this['available'] += this_hit['NumberOfAssignmentsAvailable']
				this['pending'] += this_hit['NumberOfAssignmentsPending']
				this['max'] += this_hit['MaxAssignments']
				lists_completed += ast.literal_eval(h.lists_completed)
			list_dic = {x:lists_completed.count(x) for x in lists_completed}
			this['lists'] = list_dic
			print workers			
			HIT_list.append(this)

	return(render_template('HITs.html',HITs=HIT_list))

# ----------------------------------------------------------------

#approve all assignments for this HIT
@app.route('/approveAssignments', methods=['POST'])

def approveAssignments():
	HITId = request.json['HITId']
	hits = HIT.query.filter_by(HITGroup =HITId).all()

	next_token = ''

	assignments = []

	#accumulate assignments for HITs in HITGroup
	for hit in hits:
		next_token = ''

		while next_token is not None:
			if next_token == '':
				response = client.list_assignments_for_hit(
					HITId = HITId,
					AssignmentStatuses=['Submitted'],
					MaxResults = 100,
					)
			else:
				response = client.list_assignments_for_hit(
					HITId = HITId,
					AssignmentStatuses=['Submitted'],
					MaxResults = 100,
					NextToken= next_token
					)

			current_batch,next_token = get_resources_from(response)
			assignments += current_batch


	for ass in assignments:
		response = client.approve_assignment(
			AssignmentId = ass['AssignmentId'])


	return '200'

# ----------------------------------------------------------------

#expire a given HIT
@app.route('/expireHIT', methods=['POST'])

def expireHit():
	HITId = request.json['HITId']
	hits = HIT.query.filter_by(HITGroup =HITId).all()

	#expire all HITs in HITGroup
	for hit in hits:
		response = client.update_expiration_for_hit(
	    	HITId=hit.HITId,
	    	ExpireAt=datetime(2015, 1, 1)
		)
	return '200'

# ----------------------------------------------------------------

#attempt to permanently delete HIT
@app.route('/deleteHIT', methods=['POST'])

def deleteHit():

	HITId = request.json['HITId']
	hits = HIT.query.filter_by(HITGroup =HITId).all()

	#delete all HITs in HITGroup
	for hit in hits:
		response = client.delete_hit(HITId=HITId)
	return '200'

# ----------------------------------------------------------------

#drop tables from database
@app.route('/dropTables')

def dropTables():
	db.reflect()
	db.drop_all()
	db.create_all()
	return 'Tables dropped'

# ----------------------------------------------------------------

# validate password

@app.route('/checkPassword')

def checkPassword():
	password = request.args.get('password')
	print app.config['PASSWORD']
	print password
	print password == app.config['PASSWORD']
	if password == app.config['PASSWORD']:
		return '200'
	else:
		return '400'

# ----------------------------------------------------------------

#helper for paginated client calls
def get_resources_from(response):
	results = response['Assignments']
	resources = [result for result in results]
	next_token = response.get('NextToken',None)

	return resources,next_token

# ----------------------------------------------------------------
# helper for grabbing all available qualifications

def getQualifications():
	next_token = ''

	qualifications = []

	while next_token is not None:

		if next_token == '':
			response = client.list_qualification_types(
				MustBeRequestable=True,
				MustBeOwnedByCaller=True,
				MaxResults=100
			)
		else:
			response = client.list_qualification_types(
				MustBeRequestable=True,
				MustBeOwnedByCaller=True,
				MaxResults=100,
				NextToken=next_token)

		current_batch = [{'QualID':res['QualificationTypeId'],'name':res['Name']} for res in response['QualificationTypes']]
		next_token = response.get('NextToken',None)
		qualifications += current_batch

	#print qualifications

	return qualifications

# ----------------------------------------------------------------

#connect to mturk client using AWS credentials
if debug:
	endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
else:
	endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'

client = boto3.client('mturk',endpoint_url=endpoint_url,region_name='us-east-1',aws_access_key_id=app.config['AWS_ACCESS_KEY'],aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])

@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g,'_database',None)
	if db is not None: 
		db.close()

if __name__ == "__main__":
	app.jinja_env.auto_reload = True
	app.config['TEMPLATES_AUTO_RELOAD'] = True
	app.run()
