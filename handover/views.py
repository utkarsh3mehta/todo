from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core import serializers
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.hashers import *
from django.shortcuts import get_object_or_404
import random
import datetime
import pytz
#from django.core.paginator import Paginator

from .models import User, Team, Handover, Discussion, Changetype, Changestable, Logs, Teammember, Attachments

def registerChange(string,user,hand,com=None):
    # requires a comment for assingedsomeone, assignedspoc, changedassignee, changedspoc, changedticket
    chty = Changetype.objects.get(changetypename__iexact=string)
    if string == 'created':
        comment = 'Created a new handover'
    elif string == 'resolved':
        comment = 'Resolved the handover'
    elif string == 'commented':
        comment = 'Added a new comment: ' + com
    elif string == 'priority':
        comment = 'Changed the priority'
    elif string == 'lengthydescription':
        comment = 'Added a lengthy description'
    elif string == 'shorterdescription':
        comment = 'Shortened the description'
    elif string == 'changeddescription':
        comment = 'Changed the description'
    elif string == 'removeddescription':
        comment = 'Removed the description'
    elif string == 'activated':
        comment = 'Activated the handover'
    elif string == 'removedspoc':
        comment = 'Removed SPOC details'
    elif string == 'addedticket':
        comment = 'Added ticket # ' + com + ' to the handover'
    elif string == 'removedticket':
        comment = 'Removed the assigned ticket'
    elif string == 'changedticket':
        comment = 'Changed the ticket from ' + com
    elif string == 'shorttitle':
        comment = 'Shorter title: ' + com
    elif string == 'removedtitle':
        comment = 'Removed the title!'
    elif string == 'lengthytitle':
        comment = 'Added a lengthy title: ' + com
    elif string == 'changedtitle':
        comment = 'Changed the title to: ' + com
    elif string == 'assignedself':
        comment = 'Bravo! Assigned SPOC as self'
    elif string == 'assignedspoc':
        comment = 'Assigned ' + com + ' as SPOC'
        hand.new_spoc()
    elif string == 'changedspoc':
        comment = 'Changed SPOC from ' + com
        hand.new_spoc()
    elif string == 'attached':
        comment = 'Attached ' + com
    ch = Changestable(handover=hand,changedby=user,changetypeid=chty,changecomment=comment)
    ch.save()
    user.update_respect(chty.changetypeweight)

def logChange(string,loggedby=None,relatedto=None,team=None,com=None):
    chty = Changetype.objects.get(changetypename__iexact=string)
    if string == 'userapproved':
        comment = com + ' approved the user to join team.'
    elif string == 'userdeclined':
        comment = com + ' declined the user to join team.'
    elif string == 'passwordreset':
        comment = 'Changed password from **** to ****. Seriously?'
    elif string == 'requestjointeam':
        comment = 'Requested to join team'
    elif string == 'requestleaveteam':
        comment = 'Requested to leave the team'
    elif string == 'leftteam':
        comment = 'Left the team'
    elif string == 'activateduser':
        comment = 'Activated self'
    elif string == 'deactivateduser':
        comment = 'Deactivated self'
    elif string == 'activatedteam':
        comment = 'Activated team'
    elif string == 'deactivatedteam':
        comment = 'Deactivated team'
    elif string == 'changeduserfirstname':
        comment = 'Changed first name from ' + com
    elif string == 'changeduserlastname':
        comment = 'Changed last name from ' + com
    elif string == 'addeduserlastname':
        comment = 'Added ' + com + ' as last name'
    elif string == 'removeduserlastname':
        comment = 'Removed a last name'
    elif string == 'changeduseremail':
        comment = 'Changed user email ID from ' + com
    elif string == 'changedteamemail':
        comment = 'changed team email from ' + com
    elif string == 'changedteamname':
        comment = 'changed team name from ' + com
    elif string == 'completedbasictraining':
        comment = 'Completed the basic training module'
    elif string == 'removedfromteam':
        comment = 'Removed from team'
    log = Logs(logcomment=comment,logged_by=loggedby,related_user=relatedto,related_team=team,logtypeid=chty)
    log.save()

'''
Replace a set of multiple sub strings with a new string in main string.
'''
def replaceMultiple(mainString, toBeReplaces, newString):
    # Iterate over the strings to be replaced
    for elem in toBeReplaces :
        # Check if string is in the main string
        if elem in mainString :
            # Replace the string
            mainString = mainString.replace(elem, newString)
    
    return  mainString

def index(request):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        if teams:
            context = {
                'teams': teams,
                }
            return render(request, 'handover/index.html', context)
        else:
            context = {
                'error_message':'No team exists right now. Please create one before using this application.',
            }
            return render(request,'handover/teamlogin.html', context)
    else:
        return redirect('Handover:main')

def maintenance(request):
    # get handovers resolved 30 days ago
    thirty_days = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=30)
    sixty_days = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=60)
    ninety_days = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=90)
    hand = Handover.objects.filter(resolvedon__lt=thirty_days)
    hand.delete()
    users = User.objects.all()
    noteam = []
    nologon = []
    body = {
        'noteam': {
            'email': [],
            'thirty_days': [],
            'deleted': [],
        },
        'nologon': {
            'email': [],
        },
    }
    for u in users:
        if(len(u.team.filter(teammember__is_approved=True)) == 0):
            noteam.append(u.userid)
            body['noteam']['email'].append(u.useremail)
        if(u.last_logon < ninety_days):
            nologon.append(u.userid)
            body['nologon']['email'].append(u.useremail)
    if(len(noteam) != 0):
        for usrid in noteam:
            u = User.objects.get(pk=usrid)
            if(u.last_logon < thirty_days):
                u.state(False)
                body['noteam']['thirty_days'].append(u.useremail)
                if(u.last_logon < sixty_days and not u.user_is_active):
                    u.delete()
                    body['noteam']['deleted'].append(u.useremail)
    if(len(nologon) != 0):
        for uid in nologon:
            u = User.objects.get(pk=uid)
            u.delete()
    return JsonResponse(body)

def signin(request):
    teams = Team.objects.all()
    if request.method == 'POST':
        email = request.POST['signinemail']
        password = request.POST['signinpassword']
        if not email or not password:
            context = {
                'teams': teams,
                'error_message': 'Please fill in all the details',
            }
            return render(request, 'handover/index.html', context)
        else:
            if(User.objects.filter(useremail__iexact=email).exists()):
                if(check_password(password,User.objects.get(useremail__iexact=email).userpassword)):
                    u = User.objects.get(useremail__iexact=email)
                    u.logged_in()
                    request.session['h_user'] = u.userid
                    return redirect('Handover:main')
                else:
                    context = {
                        'teams': teams,
                        'error_message': 'Wrong password',
                    }
                    return render(request, 'handover/index.html', context)
            else:
                context = {
                    'teams': teams,
                    'error_message': 'User not found',
                }
                return render(request, 'handover/index.html', context)
    else:
        context = {
            'teams': teams,
            'error_message': 'Kindly fill the sign in form',
        }
        return render(request, 'handover/index.html', context)

def createuser(request):
    if request.method == 'POST':
        firstname = request.POST['signupfirstname']
        lastname = request.POST['signuplastname']
        email = request.POST['signupemail']
        password = request.POST['signuppassword']
        team = request.POST.getlist('signupteam')
        teams = Team.objects.filter(is_active=True)
        if not firstname or not email or not password or not team:
            context = {
                'teams': teams,
                'error_message': 'Please fill in all the details',
            }
            return render(request, 'handover/index.html', context)
        else:
            hash_pass = make_password(password)
            u = User(userfirstname=firstname,userlastname=lastname,useremail=email,userpassword=hash_pass)
            try:
                u.save()
                for t in team:
                    te = Team.objects.get(pk=t)
                    u.team.add(te)
                    _to = ['utkarsh.mehta@lntinfotech.com']
                    _from = 'ild@hms.com'
                    _subject = u.useremail + ' wants to join ' + te.teamname
                    _link_approve = 'https://handoverms.westus.cloudapp.azure.com:8000/handover/approve_user/?approval=True&team='+str(te.teamid)+'&user='+str(u.userid)
                    _link_decline = 'https://handoverms.westus.cloudapp.azure.com:8000/handover/approve_user/?team='+str(te.teamid)+'&user='+str(u.userid)
                    _body = '<a href="'+_link_approve+'">Approve</a> or <a href="'+_link_decline+'">Decline</a>'
                    try:
                        send_mail(subject=_subject,message=None,html_message=_body,from_email=_from,recipient_list=_to)
                        logChange('requestjointeam',loggedby=u,relatedto=None,team=te,com=None)
                    except:
                        logChange('requestjointeam',loggedby=u,relatedto=None,team=te,com=None)
                request.session['h_user'] = u.userid
                u.logged_in()
                return redirect('Handover:main')
            except:
                context = {
                    'teams': teams,
                    'error_message': 'An error occured.',
                }
                return render(request, 'handover/index.html', context)
    else:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Kindly fill the sign in form',
        }
        return render(request, 'handover/index.html', context)

def checkuser(request):
    if request.method == 'GET':
        email = request.GET.get('useremail', None)
        data = {
            'is_taken': User.objects.filter(useremail__iexact=email).exists()
        }
        return JsonResponse(data)
    else:
        context = {
            'error_message': 'This is get',
            'link': reverse('Handover:index'),
            }
        return render(request, 'handover/ErrorPage.html', context)

def showmyself(request):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        user_id = request.session['h_user']
        user = User.objects.get(pk=user_id)
        tab = request.GET.get('tab')
        if tab == None:
            tab = 'home'
        teams = Team.objects.filter(teamid__in=Teammember.objects.filter(user=user_id,is_approved=True).values('team'))
        new_team = Team.objects.filter(is_active=True).exclude(teamid__in=Teammember.objects.filter(user=user_id).values('team'))
        changes = Changestable.objects.filter(changedby=user).order_by('-changedon')
        """ changes_paginator = Paginator(changes_list, 10, orphans=2)
        page = request.GET.get('page')
        changes = changes_paginator.get_page(page) """
        context = {
            'username': user.get_username,
            'user': user,
            'teams': teams,
            'new_team': new_team,
            'changes': changes,
            'tab': tab,
        }
        return render(request, 'handover/user.html', context)

def updateuser(request,user_id):
    if request.method == 'POST':
        if 'h_user' in request.session:
            if request.session['h_user'] == user_id:
                firstname = request.POST['updatefirstname']
                lastname = request.POST['updatelastname']
                email = request.POST['updateuseremail']
                newteam = request.POST.getlist('updateformnewteam')
                oldteam = request.POST.getlist('updateformoldteam')
                if not firstname or not email:
                    user_id = request.session['h_user']
                    user = User.objects.get(pk=user_id)
                    teams = Team.objects.filter(teamid__in=Teammember.objects.filter(user=user,is_approved=True).values('team'))
                    changes = Changestable.objects.filter(changedby=user)
                    """ changes_paginator = Paginator(changes_list, 10, orphans=2)
                    page = request.GET.get('page')
                    changes = changes_paginator.get_page(page) """
                    context = {
                        'username': user.get_username,
                        'user': user,
                        'teams': teams,
                        'changes': changes,
                        'error_message': 'Please fill in all the details',
                    }
                    return render(request, 'handover/user.html', context)
                else:
                    u = User.objects.get(pk=request.session['h_user'])
                    if firstname != u.userfirstname:
                        comment = u.userfirstname + ' to ' + firstname
                        logChange('changeduserfirstname',loggedby=u,relatedto=None,team=None,com=comment)
                        u.userfirstname = firstname
                    if u.userlastname:
                        if lastname:
                            if lastname != str(u.userlastname):
                                comment = u.userlastname + ' to ' + lastname
                                logChange('changeduserlastname',loggedby=u,relatedto=None,team=None,com=comment)
                        else:
                            logChange('removeduserlastname',loggedby=u,relatedto=None,team=None,com=None)
                            u.userlastname = None
                    else:
                        if lastname:
                            logChange('addeduserlastname',loggedby=u,relatedto=None,team=None,com=lastname)
                            u.userlastname = lastname
                    if email != u.useremail:
                        comment = u.useremail + ' to ' + email
                        logChange('changeduseremail',loggedby=u,relatedto=None,team=None,com=comment)
                        u.useremail = email
                    u.save()
                    for new in newteam:
                        if new != '':
                            nt = Team.objects.get(pk=new)
                            u.team.add(nt)
                            _to = ['utkarsh.mehta@lntinfotech.com']
                            _from = 'ild@hms.com'
                            _subject = u.get_username + ' wants to join ' + nt.teamname
                            _link_approve = 'https://handoverms.westus.cloudapp.azure.com:8000/handover/approve_user/?approval=True&team='+str(nt.teamid)+'&user='+str(u.userid)
                            _link_decline = 'https://handoverms.westus.cloudapp.azure.com:8000/handover/approve_user/?team='+str(nt.teamid)+'&user='+str(u.userid)
                            _body = '<a href="'+_link_approve+'">Approve</a> or <a href="'+_link_decline+'">Decline</a>'
                            try:
                                send_mail(subject=_subject,message=None,html_message=_body,from_email=_from,recipient_list=_to)
                                logChange('requestjointeam',loggedby=u,relatedto=None,team=nt,com=None)
                            except:
                                logChange('requestjointeam',loggedby=u,relatedto=None,team=nt,com=None)
                    for old in oldteam:
                        if old != '':
                            ot = Team.objects.get(pk=old)
                            try:
                                tm = Teammember.objects.get(user=u,team=ot)
                                tm.delete()
                                logChange('leftteam',loggedby=u,relatedto=None,team=ot,com=None)
                            except:
                                context = {
                                    'error_message': 'Nothing found!',
                                    'link': reverse('Handover:showmyself'),
                                }
                                return render(request, 'handover/ErrorPage.html', context)
                    return redirect('Handover:showmyself')
            else:
                context = {
                    'error_message': 'Sorry, you are not authorized to do this, for obvious reasons',
                    'link': reverse('Handover:showmyself'),
                }
                return render(request, 'handover/ErrorPage.html', context)
        elif 'h_user_email' in request.session:
            u = User.objects.get(useremail__iexact=request.session['h_user_email'])
            password = request.POST['resetpassword']
            hash_pass = make_password(password,salt=None)
            u.userpassword = hash_pass
            u.save()
            logChange('passwordreset',loggedby=u,relatedto=None,team=None,com=None)
            teams = Team.objects.filter(is_active=True)
            context = {
                'teams': teams,
                'message': 'Password reset successfully',
                }
            del request.session['h_user_email']
            return render(request, 'handover/index.html', context)        
    else:
        context = {
            'error_message': 'This is post.',
            'link': reverse('Handover:main'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def user_state(request,state_int):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        u = User.objects.get(pk=request.session['h_user'])
        u.state(state_int)
        return redirect('Handover:showmyself')

def forgotpassword_send_otp(request):
    if request.method == 'POST':
        useremail = request.POST['sendotpuseremail']
        if(User.objects.filter(useremail__iexact=useremail).exists()):
            u = User.objects.get(useremail__iexact=useremail)
            rand = random.randint(1000,9999)
            request.session['h_var_code'] = rand
            request.session['h_user_email'] = u.useremail
            _from = 'ild@hms.com'
            _to = [u.useremail]
            subject = 'Password reset request'
            body = 'Your pin is '+str(rand)+'.'
            try:
                send_mail(subject=subject,message=body,from_email=_from,recipient_list=_to)
                context = {
                    'reset_password_pre': 'We have sent you an OTP to your registered email ID',
                }
                return render(request, 'handover/index.html', context)
            except:
                context = {
                    'error_message': 'Error sending OTP mail. Please try again in some time.',
                }
                return render(request, 'handover/index.html', context)
            # send mail
            # send to another page ?
        else:
            teams = Team.objects.filter(is_active=True)
            context = {
                'teams': teams,
                'error_message': 'No user found with email ID ' + useremail,
            }
            return render(request, 'handover/index.html', context)
    else:
        context = {
            'error_message': 'This is post',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def forgotpassword_post_otp(request):
    if request.method == 'POST':
        otp = int(request.POST['forgotpasswordotp'])
        useremail = request.session['h_user_email']
        u = User.objects.get(useremail=useremail)
        if(request.session['h_var_code'] == otp):
            del request.session['h_var_code']
            context = {
                'reset_password_post': u,
            }
            return render(request, 'handover/index.html', context)
        else:
            context = {
                'reset_password_pre': 'Wrong OTP',
            }
            return render(request, 'handover/index.html', context)
    else:
        context = {
            'error_message': 'This is post',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)
    #else:

def approve_user(request):
    if request.method == 'GET':
        team = Team.objects.get(pk=request.GET.get('team',None))
        user = User.objects.get(pk=request.GET.get('user',None))
        approval = request.GET.get('approval',None)
        if not team or not user:
            return HttpResponse('Please give all details')
        else:
            try:
                tm = Teammember.objects.get(user=user,team=team)
                if not tm.is_approved:
                    if 'h_user' in request.session:
                        context = {
                            'current_user': User.objects.get(pk=request.session['h_user']),
                            'team': team,
                            'user': user,
                            'approval': approval,
                        }
                    else:
                        context = {
                            'team': team,
                            'user': user,
                            'approval': approval,
                        }
                    return render(request, 'handover/team_join.html', context)
                else:
                    return HttpResponse(user.userfirstname + ' is already a part of ' + team.teamname)
            except:
                return HttpResponse('Nothing found!')
    else:
        context = {
            'error_message': 'This is get',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def approve_user_post(request):
    if request.method == "POST":
        useremail = request.POST['approveuseremail']
        team = Team.objects.get(teamid=request.POST['approveteam'])
        user = User.objects.get(userid=request.POST['approveuser'])
        if useremail:
            try:
                tm = Teammember.objects.get(user=user,team=team)
                if not tm.is_approved:
                    tm.approved()
                    tm.save()
                    logChange('userapproved',loggedby=None,relatedto=user,team=team,com=useremail)
                    return HttpResponse(user.userfirstname + ' has been added to ' + team.teamname)
                else:
                    return HttpResponse(user.userfirstname + ' is already a part of ' + team.teamname)
            except:
                return HttpResponse('Nothing found!')
        else:
            context = {
                'error_message': 'Please give us your email ID.',
            }
            return render(request, 'handover/team_join.html', context)
    else:
        context = {
            'error_message': 'This is post',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def decline_user_post(request):
    if request.method == "POST":
        useremail = request.POST['approveuseremail']
        team = Team.objects.get(teamid=request.POST['approveteam'])
        user = User.objects.get(userid=request.POST['approveuser'])
        if useremail:
            try:
                tm = Teammember.objects.get(user=user,team=team)
                tm.delete()
                logChange('userdeclined',loggedby=None,relatedto=user,team=team,com=useremail)
                _to = [user.useremail]
                _from = 'ild@hms.com'
                return HttpResponse(user.userfirstname+' has been declined access to '+team.teamname)
            except:
                return HttpResponse('Nothing found!')
        else:
            context = {
                'error_message': 'Please give us your email ID.',
            }
            return render(request, 'handover/team_join.html', context)
    else:
        context = {
            'error_message': 'This is post',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def team(request):
    return render(request, 'handover/teamlogin.html')

def createteam(request):
    if request.method == 'POST':
        email=request.POST['TeamEmail']
        name=request.POST['TeamName']
        if not email or not name:
            context = {
                'error_message':'Please fill in all the details',
            }
            return render(request,'handover/teamlogin.html', context)
        else:
            t = Team(teamname=name,teamemail=email)
            try:
                t.save()
                context = {
                    'message':'Team created successfully. Now you can add users to it on the wesbites ',
                }
                return render(request, 'handover/teamlogin.html', context)
            except:
                context = {
                    'error_message':'An error occured',
                }
                return render(request,'handover/teamlogin.html', context)
    else:
        request.session['h_user'] = None
        context = {
            'error_message': 'Kindly fill the sign in form',
        }
        return render(request, 'handover/teamlogin.html', context)

def checkteam(request):
    if request.method == 'GET':
        teamemail = request.GET.get('email',None)
        if Team.objects.filter(teamemail__iexact=teamemail).exists():
            data = {
                'is_taken': Team.objects.filter(teamemail__iexact=teamemail).exists(),
                'team_name': Team.objects.get(teamemail__iexact=teamemail).teamname,
            }
            return JsonResponse(data)
        else:
            data = {
                'is_taken':Team.objects.filter(teamemail__iexact=teamemail).exists(),
            }
            return JsonResponse(data)
    else:
        context = {
            'error_message': 'This is get',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def updateteam(request):
    return HttpResponse('Trying to update team')

def main(request):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        userid = request.session['h_user']
        u = User.objects.get(pk=userid)
        if u.user_is_active:
            team = Team.objects.filter(teamid__in=(Teammember.objects.filter(user=userid,is_approved=True).values('team')),is_active=True)
            handover = Handover.objects.filter(tower__in=team,status=1).order_by('priority','tower')
            resolvedhandover = Handover.objects.filter(tower__in=team,status=3).order_by('-resolvedon')
            context = {
                'team': team,
                'handover': handover,
                'resolved': resolvedhandover,
                'user': u,
                'basictraining': not u.basictraining,
            }
            return render(request, 'handover/main.html', context)
        else:
            return redirect('Handover:showmyself')

def basictraining(request):
    if 'h_user' in request.session:
        if request.method == 'GET':
            u = User.objects.get(pk=request.session['h_user'])
            if not u.basictraining:
                logChange('completedbasictraining',loggedby=u,relatedto=None,team=None,com=None)
            u.basictraining_state()
            return redirect('Handover:main')
        else:
            context = {
                'error_message': 'This is get',
                'link': reverse('Handover:main'),
            }
            return render(request, 'handover/ErrorPage.html', context)
    else:
        context = {
            'error_message': 'Please sign in first',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def search(request):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        if request.method == "GET":
            search_string = request.GET.get('search_string', None)
            u = User.objects.get(pk=request.session['h_user'])
            t = u.team.filter(teammember__is_approved=True)
            h_description = Handover.objects.filter(tower__in=t,description__icontains=search_string)
            comments = Discussion.objects.filter(handoverid__tower__in=t,discussiontext__icontains=search_string)
            context = {
                'h_description': h_description,
                'comments': comments,
                'search_string': search_string,
            }
            return render(request, 'handover/search_output.html', context)
        else:
            context = {
                'error_message': 'This is get',
                'link': reverse('Handover:main'),
            }
            return render(request, 'handover/ErrorPage.html', context)

def newcomment(request,handover_id):
    hand = Handover.objects.get(pk=handover_id)
    createdby = User.objects.get(pk=request.session['h_user'])
    if request.method == 'POST':
        comment = request.POST['newComment']
        if comment != None:
            dis = Discussion(handoverid=hand,createdby=createdby,discussiontext=comment)
            dis.save()
            registerChange('commented',createdby,hand,comment)
            return redirect('Handover:main')
        else:
            context = {
                'team': createdby.team.filter(is_active=True),
                'hand': Handover.objects.filter(tower__in=createdby.team.filter(is_active=True)).order_by('priority'),
                'username': User.objects.get(pk=request.session['h_user']).get_username,
                'comment_error': 'Please fill this',
            }
            return render(request, 'handover/main.html', context)
    else:
        context = {
            'team': createdby.team.filter(is_active=True),
            'hand': Handover.objects.filter(tower__in=createdby.team.filter(is_active=True)).order_by('priority'),
            'username': User.objects.get(pk=request.session['h_user']).get_username,
            'comment_error': 'Please fill this first',
        }
        return render(request, 'handover/main.html', context)

def showHandoverModal(request):
    if request.method == 'GET':
        handover_id = request.GET.get('id',None)
        h = Handover.objects.get(pk=handover_id)
        if len(h.description) <= 20:
            title = h.description
        else:
            title = h.description[:18] + '...'
        # For spoc
        # If spoc is null, possibly it might throw an error
        if h.spoc is None:
            spoc = ''
        else:
            spoc = str(h.spoc.get_username)
        if h.createdby is None:
            createdby = ''
        else:
            createdby = str(h.createdby.get_username)
        # For priority #
        if h.priority == 1:
            priority = 'High'
        elif h.priority == 2:
            priority = "Medium"
        else:
            priority = "Low"
        # End for priority #
        # For status #
        if h.status == 1:
            status = 'Active'
        else:
            status = 'Resolved'
        # End for status #
        data = {
            'h_title': title,
            'h_tower': str(h.tower.teamname),
            'h_description': str(h.description),
            'h_creator': createdby,
            'h_spoc': spoc,
            'h_ticket': str(h.ticketno),
            'h_priority': priority,
            'h_status': status,
            'h_url': reverse('Handover:showhandover', args=(handover_id,))
        }
        return JsonResponse(data)
    else:
        context = {
            'error_message': 'This is get',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def showHandoverModalAttachments(request):
    if 'h_user' in request.session:
        if request.method == 'GET':
            handover_id = request.GET.get('id',None)
            h = Handover.objects.get(pk=handover_id)
            attachments = serializers.serialize('json', h.related_attachments(), fields=('path','attachcomment','uploaddate'))
            return HttpResponse(attachments, content_type='application/json')
        else:
            context = {
                'error_message': 'This is get',
                'link': reverse('Handover:index'),
            }
            return render(request, 'handover/ErrorPage.html', context)
    else:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)

"""def showHandoverModalTimeline(request):
    if 'user' in request.session:
        if request.method == 'GET':
            handover_id = request.GET.get('id',None)
            time = Changestable.objects.filter(handover=handover_id).order_by('-changedon')
            time_line = serializers.serialize('json', time, fields=('changedon','changecomment'))
            return HttpResponse(time_line, content_type='application/json')
        else:
            context = {
                'error_message': 'This is get',
                'link': reverse('Handover:index'),
            }
            return render(request, 'handover/ErrorPage.html', context)
    else:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)"""

def attachment_modal(request):
    if 'h_user' in request.session:
        if request.method == 'GET':
            handover_id = request.GET.get('id',None)
            h = Handover.objects.get(pk=handover_id)
            data = {
                'h_title': h.get_title(),
                'h_url': reverse('Handover:upload_attachment',args=(handover_id,)),
            }
            return JsonResponse(data)
        else:
            context = {
                'error_message': 'This is get',
                'link': reverse('Handover:index'),
            }
            return render(request, 'handover/ErrorPage.html', context)
    else:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)

def createhandover(request):
    team = User.objects.get(pk=request.session['h_user']).team.filter(is_active=True)
    handover = Handover.objects.filter(tower__in=team).order_by('tower','priority')
    error_message = 'An error occured. Click again to know more'
    if request.method == 'POST':
        if request.POST['handoverTower'] == '':
            context = {
                'team': team,
                'hand': handover,
                'username': User.objects.get(pk=request.session['h_user']).get_username,
                'error_message': error_message,
                'error_tower': 'Please select a team',
            }
            return render(request, 'handover/main.html', context)
        else:
            tower = Team.objects.get(pk=request.POST['handoverTower'])
        createdby = User.objects.get(pk=request.session['h_user'])
        if request.POST['handoverDescription'] == '':
            context = {
                'team': team,
                'hand': handover,
                'username': User.objects.get(pk=request.session['h_user']).get_username,
                'error_message': error_message,
                'error_description': 'Description is a mandatory field',
            }
            return render(request, 'handover/main.html', context)
        else:
            description = request.POST['handoverDescription']
        priority = int(request.POST['handoverPriority'])
        if request.POST['ticketno'] == '':
            ticket = None
        else:
            ticket = request.POST['ticketno']
        if request.POST['handoverSpoc'] == '':
            singlepoint = None
        else:
            singlepoint = User.objects.get(pk=request.POST['handoverSpoc'])
        hand = Handover(description=description,ticketno=ticket,priority=priority,createdby=createdby,tower=tower,spoc=singlepoint)
        try:
            hand.save()
            registerChange('created',createdby,hand)
            return redirect('Handover:main')
        except:
            context = {
                'team': team,
                'hand': handover,
                'username': User.objects.get(pk=request.session['h_user']).get_username,
                'error_message': 'Error saving the handover',
            }
            return render(request, 'handover/main.html', context)
    else:
        context = {
            'team': team,
            'hand': handover,
            'username': User.objects.get(pk=request.session['h_user']).get_username,
            'error_message': 'Kindly submit the handover form first',
        }
        return render(request, 'handover/main.html', context)

def teammembers(request):
    if request.method == 'GET':
        team_id = request.GET.get('team_id',None)
        user_list = User.objects.filter(userid__in=Teammember.objects.filter(team=team_id,is_approved=True,user__user_is_active=True).values('user'))
        users = serializers.serialize('json', user_list, fields=('userfirstname','userlastname','useremail','userreputation')) 
        return HttpResponse(users, content_type='application/json')
    else:
        context = {
            'error_message': 'This is get',
            'link': reverse('Handover:main'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def teammembers_user(request):
    if request.method == 'GET':
        team_id = request.GET.get('team_id',None)
        user_list = User.objects.filter(userid__in=Teammember.objects.filter(team=team_id,user__user_is_active=True))
        user_json = serializers.serialize('json', user_list, fields=('userfirstname','userlastname','useremail','userreputation'))
        """ for user in user_json:
            u = Teammembers.objects.get(team=team_id,user=user).is_approved
            user['approval_state'] = u """
        return HttpResponse(user_json, content_type='application/json')
    else:
        context = {
            'error_message': 'This is get',
            'link': reverse('Handover:index'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def showhandover(request,handover_id):
    if User.objects.get(pk=request.session['h_user']).user_is_active:
        if 'h_user' not in request.session:
            teams = Team.objects.filter(is_active=True)
            context = {
                'teams': teams,
                'error_message': 'Please sign in first',
            }
            return render(request, 'handover/index.html', context)
        else:
            h = get_object_or_404(Handover,pk=handover_id)
            if h.spoc:
                if request.session['h_user'] == h.spoc.userid:
                    h.checked()
            team = h.tower.teamid
            user = User.objects.filter(userid__in=Teammember.objects.filter(team=team,is_approved=True,user__user_is_active=True).values('user'))
            user_name = User.objects.get(pk=request.session['h_user'])
            discussion = Discussion.objects.filter(handoverid=h)
            context = {
                'handover': h,
                'users':user,
                'discussion':discussion,
                'user_name': user_name,
                }
            return render(request, 'handover/handover.html', context)
    else:
        return redirect('Handover:showmyself')

def updatehandover(request,handover_id):
    if request.method == 'POST':
        h = Handover.objects.get(pk=handover_id)
        changeby = User.objects.get(pk=request.session['h_user'])
        if request.POST['handoverDescription'] == '':
            if h.description:
                registerChange('removeddescription',changeby,h)
                changeby.refresh_from_db()
                h.description = None
        else:
            if request.POST['handoverDescription'] != str(h.description):
                if len(request.POST['handoverDescription']) > len(h.description):
                    registerChange('lengthydescription',changeby,h)
                    changeby.refresh_from_db()
                elif len(request.POST['handoverDescription']) < len(h.description):
                    registerChange('shorterdescription',changeby,h)
                    changeby.refresh_from_db()
                else:
                    registerChange('changeddescription',changeby,h)
                    changeby.refresh_from_db()
                h.description = request.POST['handoverDescription']
        if request.POST['handoverPriority'] != str(h.priority):
            registerChange('priority',changeby,h)
            changeby.refresh_from_db()
            h.priority = request.POST['handoverPriority']
        if request.POST['ticketno'] == '':
            if h.ticketno:
                registerChange('removedticket',changeby,h)
                changeby.refresh_from_db()
                h.ticketno = None
        else:
            ticket = request.POST['ticketno']
            if h.ticketno:
                if ticket != str(h.ticketno):
                    comment = f'{h.ticketno} to {ticket}'
                    registerChange('changedticket',changeby,h,comment)
                    changeby.refresh_from_db()
                    h.ticketno = ticket
            else:
                comment = f'{ticket}'
                registerChange('addedticket',changeby,h,comment)
                changeby.refresh_from_db()
                h.ticketno = ticket
        if request.POST['spoc'] == '':
            if h.spoc:
                registerChange('removedspoc',changeby,h)
                changeby.refresh_from_db()
                h.spoc = None
        else:
            spoc = User.objects.get(pk=request.POST['spoc'])
            if h.spoc:
                if spoc.userid != h.spoc.userid:
                    if spoc.userid == changeby.userid:
                        registerChange('assignedself',changeby,h,com=None)
                        changeby.refresh_from_db()
                    else:
                        comment = f'{h.spoc.get_username} to {spoc.get_username}'
                        registerChange('changedspoc',changeby,h,comment)
                        changeby.refresh_from_db()                
                    h.spoc = spoc
            else:
                if spoc.userid == changeby.userid:
                    registerChange('assignedself',changeby,h,com=None)
                    changeby.refresh_from_db()
                else:
                    comment = f'{spoc.get_username}'
                    registerChange('assignedspoc',changeby,h,comment)
                    changeby.refresh_from_db()
                h.spoc = spoc
        if request.POST['handoverdiscussion']:
            comment = request.POST['handoverdiscussion']
            dis = Discussion(handoverid=h,createdby=changeby,discussiontext=comment)
            dis.save()
            registerChange('commented',changeby,h,comment)
            changeby.refresh_from_db()
        h.save()
        h.refresh_from_db()
        return HttpResponseRedirect(reverse('Handover:showhandover', args=(h.handoverid,)))
    else:
        if 'h_user' in request.session:
            del  request.session['h_user']
        context = {
            'error_message': 'This is post',
            'link': reverse('Handover:main'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def activate(request, handover_id):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        user = User.objects. get(pk=request.session['h_user'])
        hand = Handover.objects.get(pk=handover_id)
        hand.status_changed()
        registerChange('activated',user, hand)
        return redirect('Handover:main')

def resolve(request, handover_id):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        userid = request.session['h_user']
        user = User.objects.get(pk=userid)
        hand = Handover.objects.get(pk=handover_id)
        hand.resolved(userid)
        registerChange('resolved', user,hand)
        return redirect('Handover:main')

def upload_attachment(request,handover_id):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        handover = Handover.objects.get(pk=handover_id)
        if request.method == "POST":
            comment = request.POST['attachment_comment']
            for myfile in request.FILES.getlist('file'):
                fs = FileSystemStorage()
                file_name = replaceMultiple(myfile.name,[' ','!','@','#','$','%','^','&','*','(',')','-','_','=','+','[','{',']','}',';',':','\'','"',',','<','/','?','>','~','`'],'')
                filename = fs.save(file_name, myfile)
                path = fs.url(filename)
                user = User.objects.get(pk=request.session['h_user'])
                a = Attachments(path=path,handoverid=handover,attachcomment=comment,uploadedby=user)
                a.save()
                registerChange('attached',user,handover,f'{file_name}')
            return redirect('Handover:main')
        context = {
            'handover': handover,
        }
        return render(request, 'handover/file_upload.html', context)

def send_feedback(request):
    if request.method == 'POST':
        user = User.objects.get(pk=request.session['h_user'])
        _from = 'ild@hms.com'
        _to = ['umteappdev@gmail.com']
        subject = user.get_username + " has sent a <sentiments> feedback"
        body = request.POST['feedbackcontent']
        try:
            send_mail(subject=subject,message=body,from_email=_from,recipient_list=_to)
            return redirect('Handover:main')
        except:
            context = {
                'error_message': 'Error occured while sending mail.',
                'link': reverse('Handover:main'),
            }
            return render(request, 'handover/ErrorPage.html', context)
    else:
        context = {
            'error_message': 'This is post',
            'link': reverse('Handover:main'),
        }
        return render(request, 'handover/ErrorPage.html', context)

def logout(request):
    if 'h_user' in request.session:
        del request.session['h_user']
    return redirect('Handover:index')

def test(request):
    if 'h_user' not in request.session:
        teams = Team.objects.filter(is_active=True)
        context = {
            'teams': teams,
            'error_message': 'Please sign in first',
        }
        return render(request, 'handover/index.html', context)
    else:
        return render(request, 'handover/testingpage.html')
