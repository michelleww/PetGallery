from datetime import datetime
from flask import Blueprint, render_template, url_for, request, redirect, flash
from app import webapp
import base64
import boto3
from boto3.dynamodb.conditions import Key
from werkzeug.utils import secure_filename
import os
import random


main = Blueprint('main', __name__, static_folder="static",
                 template_folder="template")

bucket = webapp.config['S3BUCKET']
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

class User():
    username = None
    
class Posts():
    posts = None
current_user = User()
current_posts = Posts()


@main.route('/', methods=['GET'])
def landing():
    return render_template("landing.html", user=current_user)


@main.route('/login',  methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            table = dynamodb.Table('Users')
            response = table.query(
                KeyConditionExpression=Key('Username').eq(username)
            )
            items = response['Items']
            if not items:
                flash('username does not exist', 'error')
                return render_template("login.html")
            
            username = items[0]['Username']
            if password == items[0]['Password']:
                current_user.username = username
                flash('login successfully', 'success')
                return redirect(url_for('main.home'))
                # return render_template("home.html")
            else:
                flash('login fail', 'error')
                return render_template("login.html")
        except Exception as e:
            webapp.logger.error(e)
            flash('login fail', 'error')
    return render_template("login.html")

@main.route('signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        table = dynamodb.Table('Users')
        response = table.query(
            KeyConditionExpression=Key('Username').eq(username)
        )
        items = response['Items']
        if items:
            flash('Username already exists, please pick a unique username', 'error')
            return render_template("signup.html")
                
        table.put_item(
            Item={
                'Username': username,
                'Password': password
            }
        )
        flash('Sign up successfully', 'success')
        return render_template('login.html')
    return render_template("signup.html")


@main.route('/logout', methods=['GET', 'POST'])
def logout():
    if not current_user or not current_user.username:
        return render_template("login.html")
    
    current_user.username = None
    return redirect(url_for('main.landing'))


@main.route('/keys', methods=['GET'])
def keys():
    keys = []
    try:
        table = dynamodb.Table('Posts')
        response = table.scan()
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        for item in items:
            keys.append(item['Key'])
    except Exception as e:
        webapp.logger.error(e)
        flash('Fail to get all keys from dynamodb', 'error')
    keys = list(set(keys))
    return render_template("keys.html", keys=keys, user=current_user)

@main.route('/home', methods=['GET'])
def home():
    try:
        table = dynamodb.Table('Posts')
        response = table.scan()
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
    except Exception as e:
        webapp.logger.error(e)
        flash('Fail to scan posts table', 'error')
    else:
        while True:
            try:
                if len(items) <= 3:
                    posts = items
                else:
                    posts = random.choices(items, k=3)
                for post in posts:
                    path = post['Image']
                    data = s3_client.get_object(Bucket=bucket, Key=path)
                    content = base64.b64encode(data['Body'].read()).decode('utf-8')
                    post['Image'] = content
            except Exception as e:
                continue
            break 
    current_posts.posts = posts
    return render_template("home.html", posts=posts, user=current_user)


@main.route('/search', methods=['GET', 'POST'])
def search():
    """ 
    Render search page template.
    Retrieve image by key in this page.

    Route URL: '/search'
    Methods: ['GET', 'POST'],
    Parameters:
        None
    Returns:
        String of search page template content with image retrieved by key.
    """
    if request.method == 'GET':
        return render_template("search.html", user=current_user)
    elif request.method == "POST":
        key = request.form.get('key')
        if not key:
            flash('Please do not enter empty value', 'error')
            return render_template("search.html", user=current_user)
        
        try:
            # get query with the key from dynamodb
            table = dynamodb.Table('Posts')
            response = table.query(
                KeyConditionExpression=Key('Key').eq(key)
            )         
            items = response['Items']

            # get image file from s3
            if items:
                post = items[0]
                path = post['Image']
                data = s3_client.get_object(Bucket=bucket, Key=path)
                content = base64.b64encode(data['Body'].read()).decode('utf-8')
                post['Image'] = content
                flash('Search image successfully', 'success')
                current_posts.posts = [post]
                return render_template("search.html", post=post, user=current_user)
            else:
                flash('Key does not exist', 'error')
                return render_template("search.html", user=current_user)
        except Exception as e:
            webapp.logger.error(e)
            flash('Fail to search image', 'error')
            return render_template("search.html", user=current_user)

@main.route('/post', methods=['GET'])
def post():
    post = {'Username':'username', 'Key':'key', 'Description': 'description', 'Image':'static/images/1.jpeg', 'Num_likes': 100}
    return render_template("post.html", post=post, liked=True, collected=True, user=current_user)
    

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    """ 
    Render upload page template.
    Upload image with key in this page.

    Route URL: '/upload'
    Methods: ['GET', 'POST'],
    Parameters:
        None
    Returns:
        String of upload page template content.
    """
    if request.method == 'GET':
        return render_template("upload.html", user=current_user)
    elif request.method == "POST":
        key = request.form.get('key')
        description = request.form.get('description')
        file =request.files.get('file')
        username = current_user.username
        if not key or not description:
            flash('Missing key or description', 'error')
            return render_template("upload.html", user=current_user)
        if not file:
            flash('Missing image file', 'error')
            return render_template("upload.html", user=current_user)
        
        filename = secure_filename(file.filename)
        file_name, file_ext = os.path.splitext(filename)
        
        if file_ext.lower() not in webapp.config['UPLOAD_EXTENSIONS']:
            flash('File type is not allowed', 'error')
            return render_template("upload.html", user=current_user)

        new_filename = key + file_ext
        new_path = username + '/' + new_filename
    
        # upload to dynamodb
        try:
            table = dynamodb.Table('Posts')
            response = table.query(
                KeyConditionExpression=Key('Key').eq(key)
            )         
            print("items:", response['Items'])
            
            if response['Items']:
                flash('Key has already exist', 'error')
                return render_template("upload.html", user=current_user)
            
            table.put_item(
                Item={
                    'Key': key,
                    'Username': username,
                    'Description': description,
                    'Image': new_path,
                    'Num_likes': 0
                }
            )
            # upload to s3
            s3_client.upload_fileobj(file, bucket, new_path)
            flash('upload post successfully', 'success')
        except Exception as e:
            webapp.logger.warning(e)
            flash('upload to dynamodb or s3 fail', 'error')
        return render_template("upload.html", user=current_user)

@main.route('/clear-all', methods=['POST'])
def clear_all():
    webapp.logger.info("delete all applicaiton data")
    
    flag = False
    # clear dynamodb db data
    try:
        # delete the table
        dynamodb.delete_table(
            TableName="Posts"
        )
        
        # recreate it
        posttable = dynamodb.create_table(
            TableName='Posts',
            KeySchema=[
                {
                    'AttributeName': 'Key',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'Username',
                    'KeyType': 'RANGE' 
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'Key',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Username',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Wait until the table exists.
        posttable.meta.client.get_waiter('table_exists').wait(TableName='Posts')
        
    except Exception as e:
        webapp.logger.error(e)
        flash('unable to clear dynamodb db data', 'error')
        flag = True
    
    # clear all s3 bucket
    try:
        s3_bucket = s3_resource.Bucket(bucket)
        s3_bucket.objects.all().delete()
    except Exception as e:
        webapp.logger.error(e)
        flash('Unable to clear image files stored in S3', 'error')
        flag = True
    
    # flash success message
    if not flag:
        flash('Delete all application data successfully', 'success')
    return redirect(url_for('main.clear_data'))
    
@main.route('/uploaded', methods=['GET'])
def uploaded():
    if not current_user or not current_user.username:
        return render_template("login.html")
    
    username = current_user.username
    table = dynamodb.Table('Posts')
    response = table.scan(
        FilterExpression=Key('Username').eq(username)
    )
    items = response['Items']
    list_keys = [item.get('Key') for item in items]


    return render_template("uploaded.html", user=current_user, keys=list_keys)

@main.route('/favourite', methods=['GET'])
def favourite():
    if not current_user or not current_user.username:
        return render_template("login.html")

    username = current_user.username
    table = dynamodb.Table('Favourite')
    response = table.scan(
        FilterExpression=Key('Username').eq(username)
    )
    items = response['Items']
    list_keys = [item.get('Key') for item in items]

    return render_template("favourite.html", user=current_user, keys=list_keys)

    
@main.route('/like', methods=['GET', 'POST'])
def like():
    if request.method == 'GET':
        return  redirect(url_for('main.home'))
    
    elif request.method == "POST":
        key = request.form.get('key')
        author = request.form.get('author')
        username = request.form.get('username')
        source = request.form.get('source')

        table = dynamodb.Table('Posts')
        response = table.update_item(
            Key={
                'Key': key,
                'Username': author
            },
            UpdateExpression="SET Num_likes = if_not_exists(Num_likes, :start) + :inc",

            ExpressionAttributeValues={
                ':inc': 1,
                ':start': 0,
            },
            ReturnValues="UPDATED_NEW"
        )
        print(response)
        for p in current_posts.posts:
            if p['Key'] == key:
                p['Num_likes'] += 1
        if source == 'home':
            return render_template("home.html", posts=current_posts.posts, user=current_user)
        else:
            return render_template("search.html", post=current_posts.posts[0], user=current_user)
    
@main.route('/collection', methods=['GET', 'POST'])
def collection():
    if not current_user or not current_user.username:
        return render_template("login.html")
    
    if request.method == 'GET':
        return  redirect(url_for('main.home'))
    
    elif request.method == "POST":
        key = request.form.get('key')
        author = request.form.get('author')
        username = request.form.get('username')
        source = request.form.get('source')

        # checking if the user has already marked as favourite.
        table = dynamodb.Table('Favourite')
        response = table.scan(
            FilterExpression=Key('Key').eq(key) & Key('Username').eq(username)
        )
        items = response['Items']
        if len(items) > 0:
            flash('Can not add to favourite more than once.', 'error')
            if source == 'home':
                return render_template("home.html", posts=current_posts.posts, user=current_user)
            else:
                return render_template("search.html", post=current_posts.posts[0], user=current_user)

        # Add favourit here
        try:
            table = dynamodb.Table('Favourite')
            
            table.put_item(
                Item={
                    'Key': key,
                    'Username': username,
                    'TimeStamp': str(datetime.now()),
                    'Img_status': 'active'
                }
            )
            flash('Add the post to favourite successfully', 'success')
        except Exception as e:
            webapp.logger.warning(e)
            flash('Fail to add the post to favourite', 'error')
            
        if source == 'home':
            return render_template("home.html", posts=current_posts.posts, user=current_user)
        else:
            return render_template("search.html", post=current_posts.posts[0], user=current_user)
    
@main.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        if not current_user or not current_user.username:
            return render_template("login.html")
        return render_template("profile.html", user=current_user)
    elif request.method == "POST":  
        new_password = request.form['password']
        try:
            table = dynamodb.Table('Users')
            response = table.update_item(
                        Key={"Username": current_user.username},
                        UpdateExpression="SET Password = :c",
                        ExpressionAttributeValues={":c":new_password},
                        ReturnValues="UPDATED_NEW"
                        )
            flash('Password Update Successful', 'success')
        except Exception as e:
            webapp.logger.error(e)
            flash('Password Update Fail', 'error')
        return render_template("profile.html", user=current_user)

@main.route('/deleteUploaded', methods=['GET', 'POST'])
def deleteUploaded():
    if request.method == 'GET':
        return render_template("uploaded.html", user=current_user)
    elif request.method == "POST":    
        key = request.form['key']
        try:
            table = dynamodb.Table('Posts')

            response = table.delete_item(
                        Key={"Key": key, 'Username':current_user.username}, 
                        ReturnValues="ALL_OLD")
            item = response['Attributes']
            # Delete from S3
            s3_client.delete_object(Bucket=bucket, Key=item['Image'])
            # Delete from the user table
            table = dynamodb.Table('Favourite')
            response = table.query(
                KeyConditionExpression=Key('Key').eq(key)
            )
            items = response['Items']
            for item in items:
                table.delete_item(
                        Key={"Key": key, 'Username':item['Username']})
            flash('Uploaded Post deletion successful', 'success')
        except Exception as e:
            webapp.logger.error(e)
            flash('Uploaded Post deletion Failed', 'error')
            
        return redirect(url_for('main.uploaded'))

@main.route('/deleteFavourite', methods=['GET', 'POST'])
def deleteFavourite():
    if request.method == 'GET':
        return render_template("favourite.html", user=current_user)
    elif request.method == "POST":    
        key = request.form['key']
        try:
            table = dynamodb.Table('Favourite')

            table.delete_item(
                        Key={"Key": key, 'Username':current_user.username}, 
                        )
            flash('Favourite Post deletion successful', 'success')
        except Exception as e:
            webapp.logger.error(e)
            flash('Favourite Post deletion failed', 'error')
        return redirect(url_for('main.favourite'))