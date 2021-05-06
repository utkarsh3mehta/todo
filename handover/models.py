# Give the user the choice to set the aging and other stuff before setting up the project. #


import datetime
from django.db import models
from django.utils import timezone

class ConfigurationValue(models.Model):
    configid = models.AutoField(db_column='configurationId', primary_key=True)
    configname = models.CharField(max_length=50)
    configvalue = models.CharField(max_length=100)

    def __str__(self):
        return self.configname

class Team(models.Model):
    teamid = models.AutoField(db_column='teamID', primary_key=True)  # Field name made lowercase.
    teamname = models.CharField(db_column='teamName', max_length=150)  # Field name made lowercase.
    teamemail = models.EmailField(db_column='teamEmail', unique=True, max_length=200)  # Field name made lowercase.
    created_on = models.DateTimeField(db_column='createdon',default=timezone.now)
    is_active = models.BooleanField(db_column='isactive',default=True)
    aging_warn = models.IntegerField(db_column='aging_warn',default=3)
    aging_danger = models.IntegerField(db_column='aging_danger',default=6)

    def __str__(self):
        return self.teamname

    def user_approval_state(self,user_id):
        return Teammember.objects.get(team=self,user=user_id).is_approved
    
    def state(self,bool):
        self.is_active = bool
        self.save()

    """ def get_manager(self):
        if Teammember.objects.filter(team=self,is_manager=True).exists()):
            return User.objects.get(userid=Teammember.objects.get(team=self,is_manager=True).values('user'))
        else:
            return 'No manager yet'

    def set_manager(self,userid):
        tm = Teammember.objects.get(team=self,user=userid)
        if Teammember.objects.filter(team=self,is_manager=True).exists():
            user = Teammember.objects.get(team=self,is_manager=True).user
            raise Exception(user.get_username + " is already the manager of this team.")
        else:
            tm.is_manager = True
            tm.save() """

    class Meta:
        db_table = 'Team'

class User(models.Model):
    userid = models.AutoField(db_column='userID', primary_key=True, unique=True)  # Field name made lowercase.
    userfirstname = models.CharField(db_column='userFirstName', max_length=50)  # Field name made lowercase.
    userlastname = models.CharField(db_column='userLastName', max_length=50, blank=True, null=True)
    userpassword = models.CharField(db_column='userpassword',max_length=150)
    useremail = models.EmailField(db_column='userEmail', unique=True, max_length=350)  # Field name made lowercase.
    userreputation = models.IntegerField(null=False,default=0)
    basictraining = models.BooleanField(default=False) # has the user done the basic training?
    usercreatedon = models.DateTimeField(default=timezone.now)
    last_logon = models.DateTimeField(default=timezone.now,blank=True, null=True)
    user_is_active = models.BooleanField(default=True, null=False)
    #is_manager = models.BooleanField(default=False)
    team = models.ManyToManyField('Team', through='Teammember')

    def __str__(self):
        return self.userfirstname

    @property
    def get_username(self):
        if(self.userlastname):
            return self.userfirstname + ' ' + self.userlastname
        else:
            return self.userfirstname

    def my_handover_unchecked(self):
        return Handover.objects.filter(spoc=self,checkedbyspoc=False,status__in=[1,2]).count()

    def my_handover(self):
        return Handover.objects.filter(spoc=self,status__in=[1,2])

    def team_approval_state(self,team_id):
        return Teammember.objects.get(user=self,team=team_id).is_approved

    def logged_in(self):
        self.last_logon = timezone.now()
        self.save()

    def update_respect(self,point):
        self.userreputation = self.userreputation + point
        self.save()

    def state(self,bool):
        self.user_is_active = bool
        self.save()

    def basictraining_state(self):
        if self.basictraining:
            self.basictraining = False
            self.save()
        else:
            self.basictraining = True
            self.save()

    class Meta:
        db_table = 'User'

class Teammember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    joined_on = models.DateTimeField(default=timezone.now, null=True)
    approved_on = models.DateTimeField(blank=True,null=True)
    #is_manager = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user}:{self.team}'

    def approved(self):
        self.is_approved = True
        self.approved_on = timezone.now()

class Handover(models.Model):
    status_choice = (
        (1,'New'),
        (3,'Resolved'),
    )
    state_choice = (
        (1,'High'),
        (2,'Medium'),
        (3,'Low'),
    )
    handoverid = models.AutoField(db_column='handoverID', primary_key=True)  # Field name made lowercase.
    title = models.CharField(max_length=100,default='***This handover has no title***',blank=False,null=False)
    description = models.CharField(max_length=500, blank=True, null=True)
    createdon = models.DateTimeField(db_column='createdOn',default=timezone.now)  # Field name made lowercase. This field type is a guess.
    ticketno = models.BigIntegerField(db_column='ticketNo', blank=True, null=True)  # Field name made lowercase.
    checkedbyspoc = models.BooleanField(db_column='checkedByAssignee',default=False)  # Field name made lowercase.
    priority = models.IntegerField(choices=state_choice,default=3,null=False) # {1:High;2:Medium;3:Low}
    status = models.IntegerField(choices=status_choice,default=1,null=False) # {1:New;3:Resolved}
    createdby = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='handoverreatedby', db_column='createdBy', blank=True, null=True)  # Field name made lowercase.
    tower = models.ForeignKey('Team', on_delete=models.CASCADE)
    spoc = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='handoverspoc', db_column='spoc', blank=True, null=True)
    resolvedby = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='handoverresolvedby', db_column='resolvedBy', blank=True, null=True)  # Field name made lowercase.
    resolvedon = models.DateTimeField(db_column='resolvedOn', blank=True, null=True)

    def __str__(self):
        if len(self.description) <= 15:
            return self.description
        else:
            return self.description[:12] + '...'

    def get_title(self):
        if len(self.description) <= 35:
            return self.description
        else:
            return self.description[:33] + '...'

    @property
    def hand_aging(self):
        if self.createdon >= timezone.now() - datetime.timedelta(days=int(self.tower.aging_warn)):
            return 1
        elif self.createdon >= timezone.now() - datetime.timedelta(days=int(self.tower.aging_danger)):
            return 2
        else:
            return 3

    @property
    def last_update(self):
        if Changestable.objects.filter(handover=self.handoverid):
            date = Changestable.objects.filter(handover=self.handoverid).order_by('-changedon')[0].changedon
            return str((timezone.now()-date).days)
        else:
            return '<N/A>'

    def has_comments(self):
        if (len(Discussion.objects.filter(handoverid=self.handoverid)) == 0):
            return False
        return True

    def related_comment(self):
        return Discussion.objects.filter(handoverid=self.handoverid).order_by('-discussiontime')

    def has_attachments(self):
        if (len(Attachments.objects.filter(handoverid=self.handoverid)) == 0):
            return False
        return True

    def related_attachments(self):
        return Attachments.objects.filter(handoverid=self.handoverid)

    def checked(self):
        self.checkedbyspoc = True
        self.save()

    def new_spoc(self):
        self.checkedbyspoc = False
        self.save()

    def status_changed(self):
        self.status = 1
        self.resolvedby = None
        self.resolvedon = None
        self.save()

    def resolved(self,user):
        u = User.objects.get(pk=user)
        self.status = 3
        self.resolvedby = u
        self.resolvedon = timezone.now()
        self.save()

    class Meta:
        db_table = 'Handover'

class Attachments(models.Model):
    attachmentid = models.AutoField(db_column='attachmentid', primary_key=True)
    path = models.TextField(db_column='attachment_path')
    uploaddate = models.DateTimeField(db_column='uploadDate',default=timezone.now)
    attachcomment = models.CharField(db_column='attachment_comment',null=True,blank=True,max_length=100)
    handoverid = models.ForeignKey('Handover', on_delete=models.CASCADE, db_column='handoverId')
    uploadedby = models.ForeignKey('User', on_delete=models.SET_NULL,null=True)

class Discussion(models.Model):
    discussionid = models.BigAutoField(db_column='discussionId', primary_key=True)  # Field name made lowercase.
    handoverid = models.ForeignKey('Handover', on_delete=models.CASCADE, db_column='handoverId')  # Field name made lowercase.
    createdby = models.ForeignKey('User', on_delete=models.SET_NULL, db_column='createdBy', blank=True, null=True)  # Field name made lowercase.
    discussiontext = models.CharField(db_column='discussionText',max_length=100)  # Field name made lowercase.
    discussiontime = models.DateTimeField(db_column='discussionTime',default=timezone.now)

    def __str__(self):
        return f'{self.handoverid}:{self.discussiontext}'

    def age(self):
        return str((timezone.now()-self.discussiontime).days)

    class Meta:
        db_table = 'Discussion'

class Changetype(models.Model):
    changetypeid = models.AutoField(db_column='changeTypeId', primary_key=True)  # Field name made lowercase.
    changetypename = models.CharField(db_column='changeTypeName', max_length=50, unique=True)  # Field name made lowercase.
    changetypeweight = models.IntegerField(db_column='changeTypeWeight',null=False, default=1)

    def __str__(self):
        return self.changetypename

    class Meta:
        db_table = 'changeType'

class Changestable(models.Model):
    changeid = models.BigAutoField(db_column='changeId', primary_key=True)  # Field name made lowercase.
    changedon = models.DateTimeField(db_column='changedOn',default=timezone.now)
    changecomment = models.CharField(db_column='changeComment',max_length=200, null=True)
    handover = models.ForeignKey('Handover', on_delete=models.CASCADE, db_column='handoverId')  # Field name made lowercase.
    changedby = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, db_column='changedBy')  # Field name made lowercase.
    changetypeid = models.ForeignKey('Changetype', on_delete=models.CASCADE, db_column='changeTypeId')  # Field name made lowercase.

    def __str__(self):
        return f'{self.changedon}:{self.handover}-{self.changecomment}'

    class Meta:
        db_table = 'changesTable'

class Logs(models.Model):
    logid = models.BigAutoField(db_column='logId', primary_key=True)
    loggedon = models.DateTimeField(db_column='loggedOn', default=timezone.now)
    logcomment = models.CharField(db_column='logComment', max_length=200, null=True)
    logged_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='loggedbyuser', db_column='loggedByUser', null=True)
    related_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='relateduser', db_column='relatedUser', null=True)
    related_team = models.ForeignKey('Team', on_delete=models.CASCADE, db_column='relatedTeam', null=True)
    logtypeid = models.ForeignKey('Changetype', on_delete=models.CASCADE, db_column='logTypeId')

    def __str__(self):
        return self.logcomment

    class Meta:
        db_table = 'logs'