from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import TemplateView
import json
import re
import boto
from boto.s3.key import Key
from django.conf import settings


class FileView(TemplateView):
    def buildTree(list, parent_id='root'):
        branch = []
        for li in list:
            if li['parent_id'] == parent_id:
                items = FileView.buildTree(list, li['text'])
                if items:
                    li['items'] = items
                branch.append(li)
        return branch

    def newfolder(request):
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key = request.POST.get('key') + '/' + request.POST.get('name') + '/'
        k = bucket.new_key(key)
        k.set_contents_from_string('')
        res = {
            'result': True,
            'message': 'New folder created successfully'
        }
        return HttpResponse(json.dumps(res), content_type="application/json")

    def deletefolder(request):
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key = request.POST.get('key')
        type = request.POST.get('type')

        if type == 'folder':
            for key in bucket.list(prefix=key):
                key.delete()
        else:
            k = bucket.delete_key(key)

        print(key)
        res = {
            'result': True,
            'message': 'Deleted successfully'
        }
        return HttpResponse(json.dumps(res), content_type="application/json")

    def getlink(request):
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key = request.POST.get('key')
        key_detail = bucket.get_key(key)
        key_url = key_detail.generate_url(0, query_auth=False, force_http=True)
        print(key_url)
        res = {
            'result': True,
            'key_url':key_url
        }
        return HttpResponse(json.dumps(res), content_type="application/json")

    def rename(request):
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        oldKey = request.POST.get('key')
        name = request.POST.get('name')
        newKey = ''

        arr = oldKey.split('/')
        index = len(arr) - 1

        for num in range(0, len(arr) - 1):
            newKey += arr[num] + '/'

        newKey += name + '/'
        # print (newKey)

        fileList = []

        if request.POST.get('type') == 'folder':
            files = bucket.list(prefix=oldKey)
            for file in files:
                fileList.append(file.name)
                # print(file.name)

            newFileList = []

            for file in fileList:
                newArr = file.split('/')
                newArr[index] = name
                result = ''
                for num in range(0, len(newArr)):
                    result += newArr[num] + '/'
                result = result[:-1]
                newFileList.append(result)

            for num in range(0, len(newFileList)):
                bucket.copy_key(newFileList[num], settings.AWS_STORAGE_BUCKET_NAME, fileList[num])
                bucket.delete_key(fileList[num])

        else:
            newKey = newKey[:-1]
            bucket.copy_key(newKey, settings.AWS_STORAGE_BUCKET_NAME, oldKey)
            bucket.delete_key(oldKey)

        res = {
            'result': True,
            'message': 'Rename successfully'
        }
        return HttpResponse(json.dumps(res), content_type="application/json")

    def urlify(s):
        s = re.sub(r"[^\w\s]", '_', s)
        s = re.sub(r"\s+", '_', s)
        return s

    def fileupload(request):

        file = request.FILES['files']
        key = request.POST.get('key')

        response = {}
        filename = FileView.urlify(file.name.split('.')[0])

        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

        contentType = file.content_type
        key_name = key + '/' + file.name

        k = Key(bucket)
        k.key = key_name

        print(key_name)

        if not k.exists():
            key = bucket.new_key(key_name)
            key.set_contents_from_string(file.read())
            key.set_metadata('Content-Type', contentType)
            key.set_acl('public-read')
            key.make_public()
            response['success'] = True;
            response['msg'] = "Successfully Uploaded";
        else:
            response['success'] = False;
            response['msg'] = "File name already exists";

        return HttpResponse(json.dumps(response), content_type="application/json")

    def filecut(request):
        response = {}
        if request.POST.get('type') != 'rootfolder':
            sourceKey = request.POST.get('sourceKey')
            destKey = request.POST.get('destKey')
            conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

            print(sourceKey)
            arrSourceKey = sourceKey.split('/')
            destKey += '/' + arrSourceKey[len(arrSourceKey) - 1]
            print(destKey)

            fileList = []

            if request.POST.get('type') == 'folder':
                files = bucket.list(prefix=sourceKey)
                for file in files:
                    fileList.append(file.name)

                newFileList = []

                for file in fileList:
                    newArr = file.split('/')
                    result = destKey + '/' + newArr[len(newArr) - 1]
                    # print(result)
                    newFileList.append(result)

                for num in range(0, len(newFileList)):
                    print (newFileList[num])
                    print (fileList[num])
                    bucket.copy_key(newFileList[num], settings.AWS_STORAGE_BUCKET_NAME, fileList[num])
                    bucket.delete_key(fileList[num])

            else:
                bucket.copy_key(destKey, settings.AWS_STORAGE_BUCKET_NAME, sourceKey)
                bucket.delete_key(sourceKey)

            response['result'] = True
            response['message'] = "Successfully Moved"
            return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            return HttpResponse(json.dumps(response), content_type="application/json")

    def filecopy(request):
        response = {}
        if request.POST.get('type') != 'rootfolder':
            sourceKey = request.POST.get('sourceKey')
            destKey = request.POST.get('destKey')
            conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

            print(sourceKey)
            arrSourceKey = sourceKey.split('/')
            destKey += '/' + arrSourceKey[len(arrSourceKey) - 1]
            print(destKey)

            fileList = []

            if request.POST.get('type') == 'folder':
                files = bucket.list(prefix=sourceKey)
                for file in files:
                    fileList.append(file.name)

                newFileList = []

                for file in fileList:
                    newArr = file.split('/')
                    result = destKey + '/' + newArr[len(newArr) - 1]
                    # print(result)
                    newFileList.append(result)

                for num in range(0, len(newFileList)):
                    print (newFileList[num])
                    print (fileList[num])
                    bucket.copy_key(newFileList[num], settings.AWS_STORAGE_BUCKET_NAME, fileList[num])

            else:
                bucket.copy_key(destKey, settings.AWS_STORAGE_BUCKET_NAME, sourceKey)

            response['result'] = True
            response['message'] = "Successfully Copied"
            return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            return HttpResponse(json.dumps(response), content_type="application/json")

    def files(request):
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        fileList = []
        url = settings.AWS_STORAGE_BUCKET_ROOT_FOLDER+"/"
        files = bucket.list(prefix=url)
        for file in files:
            fileList.append(file.name)

        objList = []

        rootdict = {
            'text': settings.AWS_STORAGE_BUCKET_ROOT_FOLDER,
            'parent_id': 'root',
            'expanded': True,
            'spriteCssClass': 'rootfolder',
            'path': "public/"
        }
        objList.append(rootdict)
        for obj in fileList:
            str = obj.split("/")
            print(obj)
            depth_level = len(str)
            path = "public"
            for index in range(0, depth_level):
                if index + 1 < depth_level:
                    if str[index + 1] != '':
                        dict = {}
                        dict['text'] = str[index + 1]
                        path = path + "/" + str[index + 1]
                        dict['parent_id'] = str[index]
                        dict['path'] = path

                        dict['expanded']=True
                        file = str[index + 1].split(".")
                        if len(file) == 1:
                            dict['spriteCssClass'] = 'folder'
                        else:
                            if file[1].lower() == "png" or file[1].lower() == "jpeg" or file[1].lower() == "jpg":
                                dict['spriteCssClass'] = 'image'
                            elif file[1].lower() == "css" or file[1].lower() == "html":
                                dict['spriteCssClass'] = 'html'
                            elif file[1].lower() == "pdf":
                                dict['spriteCssClass'] = 'pdf'
                            elif file[1].lower() == "txt":
                                dict['spriteCssClass'] = 'html'
                            else:
                                dict['spriteCssClass'] = 'html'

                        found = False
                        for object in objList:
                            if object['text'] == dict['text'] and object['parent_id'] == dict['parent_id']:
                                found = True;
                                break;
                        if not found:
                            objList.append(dict)

        ph = FileView.buildTree(objList)

        context = {
            'filelist': json.dumps(ph)
        }
        return render(request, 'file/file.html', context)
