# To-Do List
 
Creating a to-do list web application that supports related functionality. Users are able to:
 1) Log in; can also login via Google
 2) Create, delete, and edit to-do lists
 3) Create, delete, and edit items that are associated with a to-do list
 4) Manage the items in each to-do list and mark them as complete
 5) View details about each item
 6) Sort lists and items based on specific criteria

I wrote the unit tests for this application using Django's built-in testing framework which is based on and extends Python's "unittest" framework. 
This web application is being developed using Django, Python, HTML, CSS, and Bootstrap and will be deployed on Firebase. 

## Google sign-in (optional)

Local signup and login work without this. To add the "Sign in with Google" button:

1. In [Google Cloud Console](https://console.cloud.google.com/), open **Google Auth Platform**. Under **Audience**, choose External, keep it in Testing, and add your Google account as a test user.
2. Under **Clients**, create a **Web application** client with this authorized redirect URI:
   `http://127.0.0.1:8000/accounts/google/login/callback/`
   Open the app at `127.0.0.1`, not `localhost`; Google treats them as different addresses.
3. Put the client ID and secret in your `.env` (copied from `.env.example`):
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   ```
4. Restart the server with `uv run --env-file .env python todo_list_proj/manage.py runserver`. The button shows only when both values are set.
