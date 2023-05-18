from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, Comment, Group
from http import HTTPStatus

User = get_user_model()


class PostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='tg',
            description='desc',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        # Создаем неавторизованный клиент

        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateForm.user)

    def test_post_adding_to_db(self):
        """Проверка добавления поста в бд"""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
        }
        response = self.client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        # Проверка для неавторизованного юзера
        # кол-во постов не меняется
        # редирект работает
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_rewrite_post_in_db(self):
        """Проверка, что id прежний, текст - другой"""
        recent_pk = PostCreateForm.post.pk
        form_data = {
            'text': 'New text',
            'group': PostCreateForm.group.id,
        }
        self.authorized_client.post(
            reverse('posts:edit_post', kwargs={'post_id': recent_pk}),
            data=form_data,
            follow=True
        )
        old_text = Post.objects.get(pk=recent_pk).text
        self.assertEqual(old_text, 'New text')

    def test_adding_image_to_post(self):
        """Проверка что картинка прикрепляется к посту в бд"""
        # Создаем фейковый запрос с данными о посте
        form_data = {
            'text': 'TEST_TEXT',
            'image': 'gbgit.jpg'
        }
        self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertIsNotNone(Post.objects.get(text='TEST_TEXT').image)


class CommentTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.post = Post.objects.create(text='Test Post', author=cls.user)

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentTestCase.user)

    def test_comment_auth(self):
        response = self.client.post(reverse('posts:add_comment',
                                            kwargs={'post_id': self.post.id}),
                                    {'text': 'Test Comment'})
        # Проверяем, что пользователь не авторизован
        #  и получаем код 302 (перенаправление)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.client.force_login(self.user)
        response = self.client.post(reverse('posts:add_comment',
                                            kwargs={'post_id': CommentTestCase.
                                                    post.id}),
                                    {'text': 'Test Comment'})
        # Проверяем, что после авторизации пользователь
        # может комментировать и получаем код 302 (перенаправление)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_comment_post(self):
        comments_prev = Comment.objects.filter(
            post=CommentTestCase.post).count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': CommentTestCase.post.id}),
            {'text': 'Test Comment'})
        # Проверяем, что комментарий успешно отправлен
        # и получаем код 302 (перенаправление)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Проверяем, что комментарий появился на странице поста
        self.assertEqual(comments_prev + 1,
                         Comment.objects.filter(post=CommentTestCase
                                                .post).count())
