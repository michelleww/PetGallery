### Application Description

This application, built on AWS services, are designed with the primary goal of providing a platform for pet lovers to browse, share, like, collect unique pet moments for themselves and others. 

### Usability Description / How to use the app

The application frontend provides the interface that supports the following: 

  * Landing Page: shows a video of a heartwarming moment between a pet owner and her beloved dog.
  * Navigation Bar: on the top of the page, can redirect to pages with various functionalities
    * Landing page
    * Home page
    * Image search page
    * Image upload page
    * User menu dropdown consisting of the following:
      * Profile: Users can manage their accounts by resetting their account password;
      * Uploaded: Users can view a list of images they uploaded and remove images if they want;
      * Favourites: Users can view a list of images they collected/marked as favourites, the deletion operation is supported here as well;
      * Logout: Users can log out of the application.
  * Users can browse images uploaded by other users. 
  * Visitors will have limited usage of the application: they can browse the images and keys. Like and search features are also enabled for visitors.
  * To have full access to the application, a user will need to sign up by creating a new account with username/password, then log in with the newly created account by providing the correct username and password. 
  * Authenticated users can like or collect images and revisit those collections later via user menu dropdown. 
  * Authenticated users can upload their pet images with a title/key and a brief description.
  * Authenticated users can search for certain images by providing the image title/key.

### General Architecture 

Users use a web browser to send requests to the AWS API Gateway which triggers AWS Lambda functions, and an HTML page is returned that gives the web frontend where users can perform various types of operations introduced in usability description. The uploaded images are stored in AWS S3 bucket which supports searching, uploading, and retrieval. Details such as image file metadata are stored in AWS DynamoDB and scanning of the DB is performed on every single launch of the application.

The system is comprised of two components: Users and Images. The user component is built for user management, assigning proper permissions that only allows authenticated users to perform certain operations. All User data/credentials are stored in DynamoDB. The image component is built for managing existing images in the pool, and provides access, retrieval, and collection to users. 

### Background Process: 
System Data Collection for Analysis: The data recording is implemented to run as an individual background process, the point is to monitor and log existing number of posts, existing number of users who have signed up for the Administrator to track meaningful system data. Alternatively, the background script can log the number of active users - users who logged in within the last week.
Post Deletion process: The process is setup to run in background to delete certain unexpected uploaded image/content in case user posts images that does not match the requirements (i.e. non-pet images)
