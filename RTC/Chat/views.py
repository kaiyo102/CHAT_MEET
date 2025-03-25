from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from django.contrib.auth import login, authenticate
from datetime import datetime, timedelta
from .models import UserChat, ChatRoom, Message, MeetingRoom, Friends
import random
# Create your views here.
def login_chat(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                if not user.profile_picture:
                    user.profile_picture = 'profile_pictures/default.jpg'
                    user.save()
                next_url = request.GET.get('next', '/go_admin/')
                return redirect(next_url)
            else:
                now = datetime.now().date()
                if not user.profile_picture:
                    user.profile_picture = 'profile_pictures/default.jpg'
                    user.save()
                if user.day_start and user.day_end:
                    if user.block_forever == True:
                        message = "Tài khoản của bạn đã bị khóa vĩnh viễn"
                        print(1)
                        return render(request, 'chat/login.html',{'message':message})
                    elif user.day_start <= now <= user.day_end:
                        message = "Tài khoản của bạn đang tạm khóa"
                        print(2)
                        return render(request, 'chat/login.html',{'message':message})
                else:
                    print(3)
                    if user.full_name is None:
                        user.full_name = "UserChat"
                        user.save()
                    login(request, user)
                    next_url = request.GET.get('next', '/home/')

                    request.session['username'] = user.username
                    request.session['profile'] = {
                        'profile_picture': user.profile_picture.url if user.profile_picture else None,
                        'full_name': user.full_name,
                        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                        'phone_number': user.phone_number,
                        'email': user.email
                    }
                    return redirect(next_url)
        else:
            message = "Sai tài khoản hoặc mật khẩu!"
            return render(request, 'chat/login.html',{'message':message})
    return render(request, 'chat/login.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()
            
            return render(request, 'chat/login.html')
    else:
        form = SignUpForm()
    
    return render(request, 'chat/signup.html', {'form': form})

@login_required
def home(request):
    rooms = ChatRoom.objects.filter(users = request.user)
    return render(request, 'chat/home.html', {'rooms': rooms})

def search(request):
    search_query = request.POST.get('search_data', '').strip()
    if not search_query:
        return redirect('home')
    
    users = UserChat.objects.filter(
            username__icontains=search_query
        ).exclude(username = request.user.username)
    return render(request, 'chat/search.html', {
            'users': users,
            'search_query': search_query,
        })

def create_room(request, username):
    user1 = get_object_or_404(UserChat, username=request.user.username)
    user2 = get_object_or_404(UserChat, username=username)
    # Tạo tên phòng duy nhất cho mỗi cặp người dùng
    room_name = f"{min(user1.username, user2.username)}_{max(user1.username, user2.username)}"

    # Kiểm tra và lấy phòng nếu đã tồn tại
    room, created = ChatRoom.objects.get_or_create(name=room_name)

    if created:  # Nếu phòng được tạo mới
        room.users.add(user1, user2)

    messages = Message.objects.filter(room_name__name=room_name).order_by('date_added')
    pp_receiver = UserChat.objects.get(username=user2.username)
    pp_sender = UserChat.objects.get(username=user1.username)
    # Đặt username trong session (nếu cần)
    if not request.session.get('username'):
        request.session['username'] = request.user.username
    rooms = ChatRoom.objects.filter(users = request.user)

    return render(request, 'Chat/room.html', {
        'room_name': room_name,
        'messages': messages,
        'sender':pp_sender,
        'receiver':pp_receiver,
        'rooms': rooms
    })

def userpage(request):
    user = get_object_or_404(UserChat, username=request.user.username)   
    return render(request, 'user/userpage.html', {
        'user': user
    })

def mainmeetingpage(request):
    return render(request, 'meet/main.html')

def meeting(request):
    name = request.POST.get('name')
    description = request.POST.get('description')
    date = request.POST.get('date')
    time = request.POST.get('time')
    duration = request.POST.get('duration')
    code = random.randint(1000000000, 9999999999)
    print(name, description, date, time, duration, code)
    return render(request, 'meet/meet.html', {
        'name': name,
        'description': description,
        'date': date,
        'time': time,
        'duration': duration,
        'code': code
    })
