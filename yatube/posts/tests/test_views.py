from datetime import datetime
from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date = datetime.now()
        # Создадим запись в БД для проверки доступности адресов
        cls.test_author = User.objects.create_user(username='Test_author')
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        # Создаем пользователя
        # self.user = User.objects.create_user(username='Test_user')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostViewTests.test_author)
        self.test_post = Post.objects.create(
            text='Тестовый пост',
            pub_date=PostViewTests.date,
            author=PostViewTests.test_author,
            group=PostViewTests.test_group
        )

    def test_post_views_urls_uses_correct_template(self):
        """Views функции приложения posts используют соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=(PostViewTests.test_group.slug,)): 'posts/group_list.html',
            reverse('posts:profile', args=(PostViewTests.test_author.username,)): 'posts/profile.html',
            reverse('posts:post_detail', args=(self.test_post.id,)): 'posts/post_detail.html',
            reverse('posts:post_edit', args=(self.test_post.id,)): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_post_list_page_show_correct_context(self):
        """Проверка правильного вывода контекста поста в шаблоны"""
        reversed_name = {
            'posts:index': None,
            'posts:group_list': (PostViewTests.test_group.slug,),
            'posts:profile': (PostViewTests.test_author.username,),
        }
        for reverse_name, args in reversed_name.items():
            with self.subTest(reverse_name=reverse(reverse_name, args=args)):
                response = self.guest_client.get(reverse(reverse_name, args=args))
                context_post = response.context['page_obj'][0]
                self.assertEqual(context_post.text, self.test_post.text)
                self.assertEqual(context_post.pub_date, self.test_post.pub_date)
                self.assertEqual(context_post.author, self.test_post.author)

    def test_post_group_list_page_show_correct_context(self):
        """Шаблон group_list приложения posts сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:group_list', args=(PostViewTests.test_group.slug,)))
        context_group = response.context['group']
        self.assertEqual(context_group.description, self.test_post.group.description)
        self.assertEqual(context_group.title, self.test_post.group.title)

    def test_post_profile_page_show_correct_context(self):
        """Шаблон profile приложения posts сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:profile', args=(PostViewTests.test_author.username,)))
        context_count = response.context['count']
        self.assertEqual(context_count, self.test_post.author.posts.count())

    def test_post_post_detail_page_show_correct_context(self):
        """Шаблон post_detail приложения posts сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:post_detail', args=(self.test_post.id,)))
        context_post = response.context['post_detail']
        context_count = response.context['count']
        self.assertEqual(context_post.text, self.test_post.text)
        self.assertEqual(context_post.pub_date, self.test_post.pub_date)
        self.assertEqual(context_post.author, self.test_post.author)
        self.assertEqual(context_count, self.test_post.author.posts.count())

    def test_post_create_post_page_show_correct_context(self):
        """Шаблон создания и редактирования поста сформирован с правильным контекстом."""
        reversed_name = {
            'posts:post_create': None,
            'posts:post_edit': (self.test_post.id,)
        }
        for reversed_name, args in reversed_name.items():
            response = self.authorized_client.get(reverse(reversed_name, args=args))
            form_fields = {
                'text': forms.fields.CharField,
                # При создании формы поля модели типа TextField
                # преобразуются в CharField с виджетом forms.Textarea
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(reverse=reverse(reversed_name, args=args), value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_paginator_in_pages_with_posts(self):
        """Тест паджинатора на страницах с постами"""
        paginator_amount = 10
        second_page_amount = 3
        posts = [
            Post(
                text=f'text {num}', author=PostViewTests.test_author,
                group=PostViewTests.test_group
            ) for num in range(1, paginator_amount + second_page_amount)
        ]
        Post.objects.bulk_create(posts)
        paginator_page = {
            'posts:index': None,
            'posts:group_list': (PostViewTests.test_group.slug,),
            'posts:profile': (PostViewTests.test_author,),
        }
        for reverse_name, args in paginator_page.items():
            post_page = {
                paginator_amount: '',
                second_page_amount: '?page=2'
            }
            for amount, page in post_page.items():
                with self.subTest(reverse=reverse(reverse_name, args=args), amount=amount, page=page):
                    response = self.guest_client.get(reverse(reverse_name, args=args) + page)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertEqual(len(response.context['page_obj']), amount)
