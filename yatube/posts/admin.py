from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    empty_value_display = '-пусто-'
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'text', 'author', 'pk',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
