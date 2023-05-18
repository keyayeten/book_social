from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text',
                  'group',
                  'image'
                  )

        labels = {'text': 'Введите текст',
                  'group': 'Выберите группу',
                  'image': 'Картиночька'
                  }

        help_texts = {'text': 'Напишите что у вас на душе',
                      'group': 'Ну типа группы)',
                      'image': 'Тут должна быть картиночька'
                      }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
        }
