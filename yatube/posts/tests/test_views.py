from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache
from http import HTTPStatus

from ..models import Group, Post, Follow

User = get_user_model()
FIRST_PAGE_POSTS = 10
SECOND_PAGE_POSTS = 3


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:group_posts',
                    kwargs={'slug': StaticURLTests.group.slug}):
            'posts/group_list.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': StaticURLTests.post.pk}):
            'posts/post_detail.html',
            reverse('posts:profile',
                    kwargs={'username': StaticURLTests.user.username}):
            'posts/profile.html',
            reverse('posts:edit_post',
                    kwargs={'post_id': StaticURLTests.post.pk}):
                        'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_creation_page_correct_context(self):
        """Шаблон create post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={'username': self.user.username})))
        self.assertEqual(response.context.get('author'), self.user)
        self.assertEqual(response.context.get('name'), self.user.username)
        self.assertEqual(response.context.get('id'), self.user.id)
        # отсутствие картинки
        self.assertNotIn('image', response.context)

    def test_pages_contains_images(self):
        """Страницы index, group, profile, detail содержат картинку"""
        post = Post.objects.create(author=self.user,
                                   group=StaticURLTests.group,
                                   text='Test Post',
                                   image='test_image.jpg')
        responce_detail = self.client.get(reverse('posts:post_detail',
                                                  kwargs={'post_id': post.pk}))
        responce_index = self.client.get(reverse('posts:index'))
        responce_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        responce_group = self.client.get(reverse('posts:group_posts',
                                                 kwargs={'slug': StaticURLTests
                                                         .group.slug}))

        self.assertEqual(responce_detail.context['post'].image,
                         'test_image.jpg')
        self.assertIsNotNone(responce_index.context['page_obj']
                             .object_list[0].image)
        self.assertEqual(responce_profile.context['page_obj']
                         .object_list[0].image,
                         'test_image.jpg')
        self.assertEqual(responce_group.context['page_obj']
                         .object_list[0].image,
                         'test_image.jpg')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание',
        )
        posts = []
        for _ in range(13):
            post = Post(author=cls.user, text='Тестовый пост', group=cls.group)
            posts.append(post)

        Post.objects.bulk_create(posts)

    def setUp(self):
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        # pagination on groups
        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': PaginatorViewsTest
                                                 .group.slug}))
        self.assertEqual(len(response.context['page_obj'].object_list),
                         FIRST_PAGE_POSTS)
        # pagination on user
        response = self.client.get(reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(len(response.context['page_obj'].object_list),
                         FIRST_PAGE_POSTS)

    def test_second_page_contains_three_records(self):
        # pagination on groups
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug': PaginatorViewsTest
                                                   .group.slug}
                                           ) + '?page=2')
        self.assertEqual(len(response.context['page_obj'].object_list),
                         SECOND_PAGE_POSTS)
        # pagination on user
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username':
                                                   self.user.username}
                                           ) + '?page=2')
        self.assertEqual(len(response.context['page_obj'].object_list),
                         SECOND_PAGE_POSTS)


class IndexPageCacheTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')

    def test_cache_works(self):
        posts_from_cache = cache.get('index_page')
        cache.clear()
        posts_from_cache_2 = cache.get('index_page')
        self.assertEqual(str(posts_from_cache), str(posts_from_cache_2))

    def test_cache_refresh(self):
        posts_from_cache = cache.get('index_page')
        cache.clear()
        Post.objects.create(author=self.user, text='New text')
        posts_from_cache_2 = cache.get('index_page')
        if posts_from_cache is not None and posts_from_cache_2 is not None:
            self.assertNotEqual(str(posts_from_cache), str(posts_from_cache_2))


class FollowTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1')
        self.user2 = User.objects.create_user(username='user2')
        self.user3 = User.objects.create_user(username='user3')
        self.post1 = Post.objects.create(author=self.user1, text='post1')
        self.post2 = Post.objects.create(author=self.user2, text='post2')
        self.post3 = Post.objects.create(author=self.user3, text='post3')
        self.follow1 = Follow.objects.create(user=self.user1,
                                             author=self.user2)
        self.follow2 = Follow.objects.create(user=self.user3,
                                             author=self.user2)

    def test_follow(self):
        # Пользователь может подписываться на других пользователей
        self.client.force_login(self.user1)
        response = self.client.post(reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Follow.objects.filter(user=self.user1.id,
                                              author=self.user2.id).exists())

    def test_unfollow(self):
        # Пользователь может удалять других пользователей из подписок
        self.client.force_login(self.user3)
        response = self.client.post(reverse('posts:profile_unfollow',
                                            kwargs={'username':
                                                    self.user2.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(Follow.objects.filter(user=self.user3,
                                               author=self.user2).exists())

    def test_new_post_in_followers_feed(self):
        # Новая запись пользователя появляется в ленте тех,
        #  кто на него подписан
        self.client.force_login(self.user2)
        response = self.client.post(reverse('posts:create_post'),
                                    {'text': 'new_post'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.filter(author=self.user2,
                                             text='new_post').count(), 1)

        self.client.force_login(self.user1)
        response = self.client.get(reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'new_post')

        self.client.force_login(self.user3)
        response = self.client.get(reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'new_post')
