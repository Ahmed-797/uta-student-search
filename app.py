"""
This is a Flask app that allows users to search for other users and view their profiles.
"""

import os
import json
import datetime
import secrets
import requests
import pymongo
from bson import ObjectId
from flask_pymongo import PyMongo
from flask import Flask, render_template, request, make_response, redirect, url_for
#from tests.test import search_employee

app = Flask(__name__, template_folder='./templates')
app.config.from_pyfile('config.py')

config_data = os.environ if 'DB_USERNAME' in os.environ else app.config

DB_USERNAME = config_data['DB_USERNAME']
DB_PASSWORD = config_data['DB_PASSWORD']
DB_PATH = config_data['DB_PATH']
DB_NAME = config_data['DB_NAME']
DB_MODE = config_data['DB_MODE']
COURSE_FETCH_URL = config_data['COURSE_FETCH_URL']
PROGRAM_ID = config_data['PROGRAM_ID']
USER_AGENT = config_data['USER_AGENT']

app.config['DARK_MODE'] = False
app.config["MONGO_URI"] = f"{DB_MODE}://{DB_USERNAME}:{DB_PASSWORD}@{DB_PATH}/{DB_NAME}"

mongo = PyMongo(app)

@app.route('/')
def search_form():
    """Render search form template"""
    session_id = secrets.token_hex()

    # Set the session identifier as a cookie
    response = make_response(render_template('search.html', app=app))
    response.set_cookie('session_id', session_id)
    return response


@app.route('/search', methods=['GET'])
def search():
    """Search for user by name or email and return search results"""
    # Get the search query
    query = request.args.get('query')

    # Get the IP address, user agent string, and user identifier of the person who is searching
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    session_id = request.cookies.get('session_id')

    mongo.db.searches.insert_one({'query': query,
                                  'timestamp': datetime.datetime.now(),
                                  'ip_address': ip_address,
                                  'user_agent': user_agent,
                                  'session_id': session_id
                                  })

    # Build the search query using the $or operator to search all of the fields
    search_query = {
        '$or': [
            {'user_name': {'$regex': query, '$options': 'i'}},
            {'name': {'$regex': query, '$options': 'i'}},
            {'u_eid': {'$regex': query, '$options': 'i'}},
            {'email': {'$regex': query, '$options': 'i'}}
        ]
    }

    # Search the MongoDB collection for documents that match the query
    try:
        users = mongo.db.ids.find(search_query).sort([('u_eid', -1)])
        num_records = mongo.db.ids.count_documents(search_query)
    except pymongo.errors.OperationFailure:
        users, num_records = None, 0

    # If there is only one record found, redirect the user to the profile page of the user
    if num_records == 1:
        user = users[0]
        user_id = user['_id']
        return redirect(url_for('profile', user_id=user_id))

    # Render the search results template with the search results
    return render_template('search_results.html', users=users, num_records=num_records, app=app)


@app.route('/profile/<user_id>', methods=['GET', 'POST'])
def profile(user_id):
    """Render user profile template"""

    # Find the user document in the 'ids' collection
    user = mongo.db.ids.find_one({'_id': ObjectId(user_id)})

    # Find the classes for the user in the 'classes' collection
    classes = mongo.db.classes.find_one({'u_eid': user['u_eid']})
    no_classes_found = classes.get('no_classes_found', False) if classes else False
    classes = json.loads(classes['classes']) if classes else []

    is_employee =  user['email'] and user['email'].endswith('@uta.edu')

    # complete once webdriver available
    # if is_employee:
    #     split_name = user['name'].split()
    #     employee_name = f"{split_name[0]} {split_name[-1]}"
    #     records = search_employee(employee_name)
        
    #     if records:
    #         print(records)

    # Check if the user has any Spring 2023 classes
    if classes:
        spring_classes_available, semester = False, None

        for semester in classes:
            if 'Spring 2023' in semester:
                spring_classes_available = True
                break

        # If the user has Spring 2023 classes
        if spring_classes_available:
            spring_classes = semester['Spring 2023']

            # Iterate over the Spring 2023 classes
            for i, course in enumerate(spring_classes):
                branch, course_id, section_num = course.split(':') if ':' in course else course.split()

                # Create a query to find the course in the 'course_info' collection
                course_query = {
                    'course_id': course_id.strip(),
                    'section_num': str(int(section_num.strip())),
                    'branch': branch.strip()
                }
               
                # Find the course in the 'course_info' collection
                course_result = mongo.db.course_info.find_one(course_query)

                if course_result and '_id' in course_result:
                    id_found = course_result['_id']
                    spring_classes[i] += f'-{id_found}'

    # Render the profile template with the user and classes information
    return render_template('profile.html', user=user, app=app, classes=classes, no_classes_found=no_classes_found)


@app.route('/courses/<course_id>')
def courses(course_id):
    """Fetch and display course information"""

    # Find the course document in the 'course_info' collection
    course = mongo.db.course_info.find_one({'_id': ObjectId(course_id)})
    # Create a mapping of abbreviated day names to full day names
    class_days_mapping = {
        'TuTh': 'Tuesday Thursday',
        'MoWe': 'Monday Wednesday',
        'Fr': 'Friday',
        'Mo': 'Monday',
        'We': 'Wednesday',
        'Tu': 'Tuesday',
        'Th': 'Thursday',
        'Sa':  'Saturday',
        'MoWeFr' : 'Monday Wednesday Friday'
    }
    # Render the courses template with the course and class_days_mapping information
    return render_template('courses.html', app=app, course=course, class_days_mapping=class_days_mapping)


@app.route('/fetch_classes/<user_id>', methods=['POST'])
def fetch_classes(user_id):
    """Fetch and display list of classes for user"""

    user = mongo.db.ids.find_one({'_id': ObjectId(user_id)})
    u_eid = user['u_eid']
    session_id = request.cookies.get('session_id')

    # Make the API call to get the classes for the user
    term_ids = ['100072549', '100075493', '100076853']
    term_mapping = {'100072549': "Spring 2022",
                    '100075493': "Fall 2022", '100076853': "Spring 2023"}

    classes = []

    for term_id in term_ids:
        data = get_courses(term_id, u_eid)

        if not data:
            continue

        subjects = [''.join(course['ddcsBreadCrumb'].split(':')[-3:])
                    for course in data['courseSectionDTO']]
        classes.append({term_mapping[term_id]: subjects})

    # Save the classes to the 'classes' collection
    record = mongo.db.classes.find_one({'u_eid': u_eid})

    new_record = {'u_eid': u_eid, 'session_id': session_id, 'classes': json.dumps(classes), 'timestamp': datetime.datetime.now()}

    if not classes:
        new_record['no_classes_found'] = True

    if not record:
        mongo.db.classes.insert_one(new_record)
    else:
        mongo.db.classes.replace_one({'_id': record['_id']}, new_record, upsert=True)
        
    return redirect(url_for('profile', user_id=user_id))


def get_courses(term_id, uta_id):
    """Call API to get list of classes for user"""

    url = COURSE_FETCH_URL
    
    # Set the payload for the API call as a JSON object
    payload = json.dumps({"termId": term_id, "programId": PROGRAM_ID, "studentId": uta_id})
    user_agent = USER_AGENT
    headers = {'User-Agent': user_agent,'Content-Type': 'application/json'}

    response = requests.request("POST", url, headers=headers, data=payload, timeout=30)

    # Try to parse the JSON response
    try:
        result = response.json()[0]
    # If the response is not a valid JSON object
    except KeyError:
        result = None

    return result

