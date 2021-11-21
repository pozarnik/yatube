from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User
from .forms import PostForm
# users/views.py


# Импортируем класс формы, чтобы сослаться на неё во view-классе


def authorized_only(func):
    # Функция-обёртка в декораторе может быть названа как угодно
    def check_user(request, *args, **kwargs):
        # В любую view-функции первым аргументом передаётся объект request,
        # в котором есть булева переменная is_authenticated,
        # определяющая, авторизован ли пользователь.
        if request.user.is_authenticated:
            # Возвращает view-функцию, если пользователь авторизован.
            return func(request, *args, **kwargs)
        # Если пользователь не авторизован — отправим его на страницу логина.
        return redirect('/auth/login/')        
    return check_user

def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all().order_by('-pub_date')
    # Если порядок сортировки определен в классе Meta модели,
    # запрос будет выглядить так:
    # post_list = Post.objects.all()
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10) 

    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')

    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
    }
    # posts = Post.objects.order_by('-pub_date')[:10]
    # context = {
    #     'posts': posts,
    # }
    return render(request, template, context) 

def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context) 

def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user)
    count= post_list.count()
    paginator = Paginator(post_list, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'username': user,
        'count': count,
        'page_obj': page_obj,
    }
    return render(request, template, context)

def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_detail = Post.objects.get(pk=post.id)
    count = Post.objects.filter(author=post.author).count()
    context = {
        'count': count,
        'post_detail': post_detail,
        'post': post,
    }
    return render(request, template, context)

def post_create(request):
    template = 'posts/create_post.html'
    # Проверяем, получен POST-запрос или какой-то другой:
    if request.method == 'POST':
        # Создаём объект формы класса ContactForm
        # и передаём в него полученные данные
        form = PostForm(request.POST)

        # Если все данные формы валидны - работаем с "очищенными данными" формы
        if form.is_valid():
            # Берём валидированные данные формы из словаря form.cleaned_data
            text = form.cleaned_data['text']
            group = form.cleaned_data['group']
            # При необходимости обрабатываем данные
            new_post = Post.objects.create(
                author=request.user, 
                text=text, 
                group=group
            )
            # сохраняем объект в базу
            new_post.save()
            
            # Функция redirect перенаправляет пользователя 
            # на другую страницу сайта, чтобы защититься 
            # от повторного заполнения формы
            return redirect (f'/profile/{request.user}/')

        # Если условие if form.is_valid() ложно и данные не прошли валидацию - 
        # передадим полученный объект в шаблон,
        # чтобы показать пользователю информацию об ошибке

        # Заодно заполним все поля формы данными, прошедшими валидацию, 
        # чтобы не заставлять пользователя вносить их повторно
        return render(request, template, {'form': form})

    # Если пришёл не POST-запрос - создаём и передаём в шаблон пустую форму
    # пусть пользователь напишет что-нибудь
    form = PostForm()
    return render(request, template, {'form': form}) 

def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'GET':
        if request.user != post.author:
            return redirect (f'/posts/{post_id}/')
        form = PostForm(instance=post)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if request.user != post.author:
            return redirect (f'/posts/{post_id}/')
        if form.is_valid():
            form.save()
        return redirect (f'/posts/{post_id}/')
    context = {
        'form': form,
        'post_id': post_id,
        'is_edit': 'is_edit',
    }
    return render(request, template, context)