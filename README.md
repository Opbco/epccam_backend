# epccam_backend (API)
API develop with Python (Flask) and Postgres RDS to manage information about pastors of Cameroon Presbyterian Church

## Getting Started

### Pre-requisites and Local Development

Developers using this project should already have Python3, pip and node installed on their local machines.

#### prerequisites

- run `pip install requirements.txt`. All required packages are included in the requirements file.
- create an .env file with the JWT_SECRET value.

### Running the server

ensure you are working using your created virtual environment.

To run the server, execute:

```
export FLASK_APP=flaskr
export FLASK_ENV=development
flask run
```

These commands put the application in development and directs our application to use the `__init__.py` file in our flaskr folder. Working in development mode shows an interactive debugger in the console and restarts the server whenever changes are made. If running locally on Windows, look for the commands in the [Flask documentation](http://flask.pocoo.org/docs/1.0/tutorial/factory/).

The application is run on `http://127.0.0.1:5000/` by default and is a proxy in the frontend configuration.


# Still working on it. will complete, step by step
