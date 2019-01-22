from manage import app, db

class HIT(db.Model):
    __tablename__ = 'HITs'

    HITId = db.Column(db.String(64), primary_key=True)
    title = db.Column(db.String(128),unique=False)
    lists = db.Column(db.String(128),unique=False)
    lists_distributed = db.Column(db.String(128),unique=False)
    lists_completed = db.Column(db.String(128),unique=False)
    timeout = db.Column(db.Integer,unique=False)
    ibexURL = db.Column(db.String(120),unique=False)
    batch = db.Column(db.Integer,unique=False)
    maxNum = db.Column(db.Integer,unique=False)
    surveyCode = db.Column(db.String(64),unique=False)
    numGrabbed = db.Column(db.Integer,unique=False)
    HITGroup = db.Column(db.String(64),unique=False)
    created = db.Column(db.DateTime,unique=False)

    def __repr__(self):
        return '<HIT %r>' % (self.HITId)
    def __init__(self,HITId = None,title=None,lists=None,lists_distributed=None,lists_completed=None,timeout=None,ibexURL=None,batch=None,maxNum=None,surveyCode=None,numGrabbed=None,HITGroup=None,created=None):
       self.HITId = HITId
       self.title = title
       self.lists = lists 
       self.lists_distributed = lists_distributed
       self.lists_completed = lists_completed
       self.timeout = timeout
       self.ibexURL = ibexURL
       self.batch = batch
       self.maxNum = maxNum
       self.surveyCode = surveyCode
       self.numGrabbed = numGrabbed
       self.HITGroup = HITGroup
       self.created = created


class submit(db.Model):
    __tablename__ = 'submits'

    assignment = db.Column(db.String(64), primary_key=True)
    worker = db.Column(db.String(64),unique=False)
    hit = db.Column(db.String(64),unique=False)
    list = db.Column(db.Integer,unique=False)
    submitted = db.Column(db.Integer,unique=False)

    def __repr__(self):
        return '<submit %r>' % (self.assignment)

    def __init__(self,assignment = None,worker = None,hit=None,list=None,submitted=None):
        self.assignment = assignment
        self.worker = worker
        self.hit = hit
        self.list = list
        self.submitted=submitted

