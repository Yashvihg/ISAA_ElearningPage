from datetime import timezone
from django.contrib.auth import authenticate,login as auth_login, logout as auth_logout
from django.contrib.auth import decorators
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.http import JsonResponse,Http404, response
from django.forms.models import model_to_dict
from django.conf import settings
from .models import *
from .forms import *
import json
import random
import string
from io import BytesIO
from django.core.files import File
from html2image import Html2Image
from PIL import Image
from uuid import uuid1
from django.template.defaulttags import register, regroup
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt,ensure_csrf_cookie

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

def home(request):
    # print(request.user.user_email)
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return render(request,'learnerApp/home.html')

# @csrf_exempt
# def login(request):
#     if request.user.is_authenticated :
#         return redirect('dashboard')
#     else:
#         if(request.method == 'POST'):
#             user_data = json.loads(request.body)
#             print(user_data)
#             user = authenticate(username=user_data['username'],password=user_data['password'])
#             if user is None:
#                 return JsonResponse({'message':"Invalid Email or Password"},status="500")
#             else:
#                 auth_login(request,user)
#                 # return JsonResponse({'message':"success"})
#                 return redirect('dashboard')
#         else:
#             return render(request,'learnerApp/login.html')

@csrf_exempt
def login(request):
    if request.user.is_authenticated :
        return redirect('dashboard')
    else:
        if(request.method == 'POST'):
            username = request.POST.get('username')
            password = request.POST.get('password')
            # print(user_data)
            user = authenticate(username=username,password=password)
            if user is None:
                return JsonResponse({'message':"Invalid Email or Password"},status="500")
            else:
                auth_login(request,user)
                # return JsonResponse({'message':"success"})
                return redirect('dashboard')
        else:
            return render(request,'learnerApp/login.html')

def logout(request):
    auth_logout(request)
    return redirect('home')

def get_random_string():
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(8))
    return result_str

def allUser(request):
    # print(CustomUser.objects.all())
    # print("institutes")
    # print(Institute.objects.all())
    for i in CustomUser.objects.all():
        print(model_to_dict(i))
    # print(model_to_dict(Student.objects.get(user=CustomUser.objects.get(user_email="swati@gmail.com"))))
    # print(Student.objects.get(user=CustomUser.objects.get(user_email="swati@gmail.com")).institute)
    return render(request,'learnerApp/adminDashboard.html')

def adminDashboard(request):
    try:
        instituteList = Institute.objects.all()
        return render(request,'learnerApp/adminDashboard.html',context={'user':request.user,'instituteList':instituteList})
    except:
        return redirect('createAdmin')
def instituteDashboard(request):
    facultyList = Faculty.objects.filter(institute= Institute.objects.get(user=request.user))
    return render(request,'learnerApp/instituteDashboard.html',context={'user':request.user,'facultyList':facultyList})

def facultyDashboard(request):
    # return render(request,'learnerApp/facultyDashboard.html',context={'user':request.user})
    return studentList(request)

def studentDashboard(request):
    return redirect('classroomList')

# @login_required(login_url="/login/")
def dashboard(request):
    # print(request.user.is_authenticated)
    if request.user.is_admin:
        return adminDashboard(request)
    elif request.user.is_institute:
        return instituteDashboard(request)
    elif request.user.is_faculty:
        return facultyDashboard(request)
    elif request.user.is_student:
        return studentDashboard(request)
    else:
        raise Http404("User role does not exist")

@login_required(login_url="/login/")
def profile(request):
    if request.method == 'POST':
        form = None
        if request.user.is_admin:
            form = AdminForm(request.POST,request.FILES,instance=Admin.objects.get(user=request.user))
        elif request.user.is_institute:
            form = InstituteForm(request.POST,request.FILES,instance=Institute.objects.get(user=request.user))
        elif request.user.is_faculty:
            form = FacultyForm(request.POST,request.FILES,instance=Faculty.objects.get(user=request.user))
        elif request.user.is_student:
            form = StudentForm(request.POST,request.FILES,instance=Student.objects.get(user=request.user))
        else:
            raise Http404("User role does not exist")   
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        return redirect('dashboard')  
    else:
        form = None
        if request.user.is_admin:
            instance = Admin.objects.get(user=request.user)
            form = AdminForm(instance=instance)
        elif request.user.is_institute:
            instance = Institute.objects.get(user=request.user)
            form = InstituteForm(instance=instance)
        elif request.user.is_faculty:
            instance = Faculty.objects.get(user=request.user)
            form = FacultyForm(instance=instance)
        elif request.user.is_student:
            instance = Student.objects.get(user=request.user)
            form = StudentForm(instance=instance)
        extemp = getBasetemp(request)
        image = instance.user_image.url
        return render(request,'learnerApp/profile.html',context={'user':request.user,'image':image,'form':form,'extemp':extemp})
    
def getBasetemp(request):
    if request.user.is_admin:
        extemp = "learnerApp/adminDashboard.html"
    elif request.user.is_institute:
        extemp = "learnerApp/instituteDashboard.html"
    elif request.user.is_faculty:
        extemp = "learnerApp/facultyDashboard.html"
    elif request.user.is_student:
        extemp = "learnerApp/studentDashboard.html"
    return extemp

@login_required(login_url="/login/")
def addInstitute(request):
    if request.method == "POST":
        password = get_random_string()
        user  = CustomUser.objects.create_user(user_email=request.POST.get('user_email'),role="institute",password=password)
        user.save()
        institute_name = request.POST.get('institute_name')
        obj = Institute.objects.create(user=user,institute_name=institute_name,institute_address=request.POST.get('institute_address'),institute_id=request.POST.get('institute_id'))
        sendPass(institute_name,user.user_email,password)
        createImage(request.POST.get('institute_name'))
        im = Image.open(settings.MEDIA_ROOT+'/learnerApp/images/test.png')
        blob = BytesIO()
        im.save(blob,'PNG')
        blob.seek(0)
        name = str(uuid1())+'.png'
        imfile = File(blob,name=name)
        obj.user_image.save(name,imfile,save=True)
        obj.save()
        return redirect('dashboard')
    else:
        extraFields = [
            {
                'label':"Institute Name",
                'name':'institute_name',
                'type':'text'
            },
            {
                'label':"Institute Id",
                'name':'institute_id',
                'type':'number'
            },
            {
                'label':"Institute Address",
                'name':'institute_address',
                'type':'text'
            },
            {
                'label':"Institute Number",
                'name':'institute_number',
                'type':'number'
            }
        ]
        extemp = getBasetemp(request)
        return render(request,'learnerApp/addUser.html',context={'extraFields':extraFields,'extemp':extemp})

@login_required(login_url="/login/")
def addFaculty(request):
    if request.method == "POST":
        password = get_random_string()
        user  = CustomUser.objects.create_user(user_email=request.POST.get('user_email'),role="faculty",password=password)
        user.save()
        institute = Institute.objects.get(user=request.user)
        faculty_id = request.POST.get('faculty_id')
        faculty_number = request.POST.get('faculty_number')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        obj = Faculty.objects.create(user=user,faculty_id=faculty_id,faculty_number=faculty_number,first_name=first_name,last_name=last_name,institute=institute)
        last_name = request.POST.get('last_name') if request.POST.get('last_name') else ""
        sendPass(request.POST.get('first_name')+" "+ last_name,request.POST.get('user_email'),password)
        createImage(request.POST.get('first_name')+" "+ last_name)
        im = Image.open(settings.MEDIA_ROOT+'/learnerApp/images/test.png')
        blob = BytesIO()
        im.save(blob,'PNG')
        blob.seek(0)
        name = str(uuid1())+'.png'
        imfile = File(blob,name=name)
        obj.user_image.save(name,imfile,save=True)
        obj.save()
        return redirect('dashboard')
    else:
        extraFields = [
            {
                'label':"First Name",
                'name':'first_name',
                'type':'text'
            },
            {
                'label':"Last Name",
                'name':'last_name',
                'type':'text'
            },
            {
                'label':"Faculty Id",
                'name':'faculty_id',
                'type':'text'
            },
            {
                'label':"Faculty Number",
                'name':'faculty_number',
                'type':'number'
            }
        ]
        extemp = getBasetemp(request)
        return render(request,'learnerApp/addUser.html',context={'extraFields':extraFields,'extemp':extemp})

@login_required(login_url="/login/")
def studentList(request):
    if request.user.is_institute:
        studentList = Student.objects.filter(institute= Institute.objects.get(user=request.user))
    elif request.user.is_faculty:
        studentList = Student.objects.filter(institute=Faculty.objects.get(user=request.user).institute)
    extemp = getBasetemp(request)
    return render(request,'learnerApp/studentList.html',context={'user':request.user,'studentList':studentList,'extemp':extemp})

@login_required(login_url="/login/")
def classroomList(request):
    if request.user.is_faculty:
        classroomList = Classroom.objects.filter(faculty=Faculty.objects.get(user=request.user))
    elif request.user.is_student:
        classroomList = Student.objects.get(user=request.user).classrooms.all()
    extemp = getBasetemp(request)
    return render(request,'learnerApp/classroomList.html',context={'user':request.user,'classroomList':classroomList,'extemp':extemp})

@login_required(login_url="/login/")
def addClassroom(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        faculty = Faculty.objects.get(user=request.user)
        createImage(title)
        im = Image.open(settings.MEDIA_ROOT+'/learnerApp/images/test.png')
        blob = BytesIO()
        im.save(blob,'PNG')
        blob.seek(0)
        name = str(uuid1())+'.png'
        imfile = File(blob,name=name)
        obj = Classroom.objects.create(faculty=faculty,title=title)
        obj.classroom_image.save(name,imfile,save=True)
        obj.save()
        return redirect('classroom',obj.classroom_id)
    else:
        return render(request, 'learnerApp/addClassroom.html')

@login_required(login_url="/login/")
def addStudent(request):
    if request.method == "POST":
        password = get_random_string()
        user  = CustomUser.objects.create_user(user_email=request.POST.get('user_email'),role="student",password=password)
        user.save()
        if request.user.is_institute:
            institute = Institute.objects.get(user=request.user)
        elif request.user.is_faculty:
            institute = Faculty.objects.get(user=request.user).institute
        else:
            raise Http404("User does not have permission to add student")
        student_id = request.POST.get('student_id')
        student_number = request.POST.get('student_number')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        obj = Student.objects.create(user=user,first_name=first_name,last_name=last_name,student_id=student_id,student_number=student_number,institute=institute)
        last = request.POST.get('last_name') if request.POST.get('last_name') else ""
        createImage(first_name+" "+ last)
        sendPass(first_name+" "+ last,user.user_email,password)
        im = Image.open(settings.MEDIA_ROOT+'/learnerApp/images/test.png')
        blob = BytesIO()
        im.save(blob,'PNG')
        blob.seek(0)
        name = str(uuid1())+'.png'
        imfile = File(blob,name=name)
        obj.user_image.save(name,imfile,save=True)
        obj.save()
        return redirect('studentList')
    else:
        extraFields = [
            {
                'label':"First Name",
                'name':'first_name',
                'type':'text'
            },
            {
                'label':"Last Name",
                'name':'last_name',
                'type':'text'
            },
            {
                'label':"Student Id",
                'name':'student_id',
                'type':'text'
            },
            {
                'label':"Student Number",
                'name':'student_number',
                'type':'number'
            }
        ]
        extemp = getBasetemp(request)
        return render(request,'learnerApp/addUser.html',context={'extraFields':extraFields,'extemp':extemp})

def createImage(title):
    lis = title.strip().split(" ")
    if len(lis) == 1:
        initials = lis[0][:2]
    else:
        initials = lis[0][0] + lis[1][0]
    html ="""<html>
    <head></head>
    <body><p>{initials}</p></body>
    </html>"""
    html = html.format(initials=initials)
    css = """
        *{
            width:2000px;
            height2000px;
            margin:0;
        }
        p{background-color:	#c12929;
        width:100%;
        height:60%;
        padding:20% 0;
        font-family: 'Calibri', sans-serif;
        color:white;
        text-align:center;
        line-height:100%;
        font-size:20em;
        }
        """
    hti = Html2Image(output_path=settings.MEDIA_ROOT+'/learnerApp/images/')
    hti.screenshot(html_str=html, css_str=css, save_as='test.png',size=(5000,5000))
    return None

def classFeedView(request,id):
    try:
        classroom = Classroom.objects.get(pk=id)    
    except:
        return redirect('dashboard')
    extemp = getBasetemp(request)
    if request.method == 'POST':
        sender = request.user
        message = request.POST.get('message')
        if(len(message)>0):
            ClassFeedMessage.objects.create(classroom=classroom,sender=sender,message=message)
        return redirect('classFeed',id)

    messages = ClassFeedMessage.objects.filter(classroom=classroom).order_by('timestamp')
    print(messages)
    return render(request,'learnerApp/classFeed.html',context={'id':id,'extemp':extemp,'classroom':classroom,'messages':messages})

def classMaterialView(request,id):
    try:
        classroom = Classroom.objects.get(pk=id)    
    except:
        return redirect('dashboard')
    extemp = getBasetemp(request)
    materials = ClassMaterial.objects.filter(classroom=classroom)
    print(materials)
    return render(request,'learnerApp/classMaterial.html',context={'id':id,'extemp':extemp,'classroom':classroom,'materials':materials})

def classMembersView(request,id):
    try:
        classroom = Classroom.objects.get(pk=id)
    except:
        return redirect('dashboard')
    extemp = getBasetemp(request)
    if request.method == 'POST':
        try:
            user = CustomUser.objects.get(user_email=request.POST.get('user_email'))
            faculty = Faculty.objects.get(user=request.user)
            student = Student.objects.get(user=user,institute=faculty.institute)
            classroom.students.add(student)
            classroom.save()
            return redirect('classMembers',id)
        except:
            return render(request,'learnerApp/classMembers.html',context={'id':id,'extemp':extemp,'classroom':classroom,'error':"Entered Email ID is Incorrect"})
    print(classroom.students.all())
    return render(request,'learnerApp/classMembers.html',context={'id':id,'extemp':extemp,'classroom':classroom,'students':classroom.students.all()})

def classFacultyTransfer(request,id):
    try:
        classroom = Classroom.objects.get(pk=id)
        presentFaculty = Faculty.objects.get(user=request.user)
    except:
        return redirect('dashboard')
    try:
        newFaculty = request.POST.get('user_email')
        userInst = CustomUser.objects.get(user_email=newFaculty)
        faculty = Faculty.objects.get(user = userInst)
        classroom.faculty = faculty
        classroom.save()
        return redirect('classroomList')
    except:
        return redirect('classMembers',id=id)
    return redirect('dashboard')

def classAddMaterial(request,id):
    extemp = getBasetemp(request)
    if request.method == 'POST':
        classroom = Classroom.objects.get(classroom_id=id)
        title = request.POST.get('title')
        material = request.FILES.get('material')
        print(material)
        print(request.FILES)
        classMaterial = ClassMaterial.objects.create(title=title,classroom=classroom)
        classMaterial.material.save(str(uuid1()) +'.'+ material.name.split('.')[-1],material)
        return redirect('classMaterial',id)
    else:
        return render(request,'learnerApp/addClassMaterial.html',context={'extemp':extemp})

def clearMaterial(request):
    ClassMaterial.objects.all().delete()
    redirect('dashboard')

def classMaterialDiscussion(request,id,mid):
    try:
        material = ClassMaterial.objects.get(material_id=mid)
        classroom = Classroom.objects.get(pk=id)
    except:
        return redirect('dashboard')
    extemp = getBasetemp(request)
    if request.method == 'POST':
        sender = request.user
        message = request.POST.get('message')
        if(len(message)>0):
            ClassMaterialMessage.objects.create(material=material,sender=sender,message=message)
        return redirect('classMaterialDiscussion',id,mid)

    messages = ClassMaterialMessage.objects.filter(material=material).order_by('timestamp')
    print(messages)
    return render(request,'learnerApp/classMaterialDiscussion.html',context={'id':id,'extemp':extemp,'messages':messages,'material':material,'classroom':classroom})


def createAdmin(request):
    Admin.objects.create(user=request.user)
    return redirect('dashboard')

def sendPass(name,email,password):
    print(password)
    subject = 'Welcome to E-class'
    message = f'''Hi {name},You have been registered to E-class.
    your username: {email}
    your password: {password}'''
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email, ]
    send_mail( subject, message, email_from, recipient_list, fail_silently=True )

def classCallView(request,id):
    try:
        classroom = Classroom.objects.get(pk=id)
    except:
        return redirect('dashboard')
    extemp = getBasetemp(request)
    if request.user.is_faculty:
        user = Faculty.objects.get(user=request.user)
    else:
        user = Student.objects.get(user=request.user)
    return render(request,'learnerApp/videoCall.html',context={'id':id,'extemp':extemp,'classroom':classroom,'meet':json.dumps({'data':classroom.classroom_id,'email':request.user.user_email,'name':user.first_name + user.last_name})})
