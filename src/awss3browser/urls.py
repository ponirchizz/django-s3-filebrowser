from django.conf.urls import url

from . import views , file_view

urlpatterns = [
    url(r'^files/$', file_view.FileView.files, name='files'),
    url(r'^files/newfolder/$', file_view.FileView.newfolder, name='newfolder'),
    url(r'^files/deletefolder/$', file_view.FileView.deletefolder, name='deletefolder'),
    url(r'^files/rename/$', file_view.FileView.rename, name='rename'),
    url(r'^files/fileupload/$', file_view.FileView.fileupload, name='fileupload'),
    url(r'^files/filecopy/$', file_view.FileView.filecopy, name='filecopy'),
    url(r'^files/filecut/$', file_view.FileView.filecut, name='filecut'),
    url(r'^files/getlink/$', file_view.FileView.getlink, name='getlink'),
]
