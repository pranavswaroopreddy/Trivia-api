import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def get_paginated_questions(request, questions, num_of_questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * num_of_questions
    end = start + num_of_questions

    questions = [question.format() for question in questions]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={'/': {'origins': '*'}})

    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def get_all_categories():

        # This endpoint returns all categories

        try:
            categories = Category.query.all()
            category_dict = {}
            for category in categories:
                category_dict[category.id] = category.type

            return jsonify({
                'success': True,
                'categories': category_dict
            }), 200
        except Exception:
            abort(500)

    @app.route('/questions')
    def get_questions():
        # get paginated questions and categories
        questions = Question.query.order_by(Question.id).all()
        total_questions = len(questions)
        categories = Category.query.order_by(Category.id).all()

        current_questions = get_paginated_questions(
            request, questions,
            QUESTIONS_PER_PAGE)

        if (len(current_questions) == 0):
            abort(404)

        category_dict = {}
        for category in categories:
            category_dict[category.id] = category.type

        return jsonify({
            'success': True,
            'total_questions': total_questions,
            'categories': category_dict,
            'questions': current_questions
        }), 200

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.get(id)
            question.delete()

            return jsonify({
                'success': True,
                'message': "Question successfully deleted"
            }), 200
        except Exception:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        # Get data from request
        data = request.get_json()

        question = data.get('question', '')
        answer = data.get('answer', '')
        difficulty = data.get('difficulty', '')
        category = data.get('category', '')

        # if data is empty abort with 400
        if ((question == '') or (answer == '')
                or (difficulty == '') or (category == '')):
            abort(400)

        try:
            # Create a new question instance
            question = Question(
                question=question,
                answer=answer,
                difficulty=difficulty,
                category=category)

            # save question
            question.insert()

            # return success message
            return jsonify({
                'success': True,
                'message': 'Question created!'
            }), 201

        except Exception:
            abort(500)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()
        search_term = data.get('searchTerm', '')

        # if empty return 400 bad request
        if search_term == '':
            abort(400)

        try:
            questions = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            # if there are no questions for search term return 404
            if len(questions) == 0:
                abort(404)

            # paginate questions
            paginated_questions = get_paginated_questions(
                request, questions,
                QUESTIONS_PER_PAGE)

            # return response if successful
            return jsonify({
                'success': True,
                'questions': paginated_questions,
                'total_questions': len(Question.query.all())
            }), 200

        except Exception:
            # This error code is returned when 404 abort
            # raises exception from try block
            abort(404)

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):
        """This endpoint handles getting questions by category"""

        # get the category by id
        category = Category.query.filter_by(id=id).one_or_none()

        # abort 400 for bad request if category isn't found
        if (category is None):
            abort(422)

        questions = Question.query.filter_by(category=id).all()

        # paginate questions
        paginated_questions = get_paginated_questions(
            request, questions,
            QUESTIONS_PER_PAGE)

        # return the results
        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions),
            'current_category': category.type
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz_question():
        """This returns a random question to play quiz."""

        # process the request data and get the values
        data = request.get_json()
        previous_questions = data.get('previous_questions')
        quiz_category = data.get('quiz_category')

        # return 404 if quiz_category or previous_questions is empty
        if ((quiz_category is None) or (previous_questions is None)):
            abort(400)

        # if default value of category is given return all questions
        # else return questions filtered by category
        if (quiz_category['id'] == 0):
            questions = Question.query.all()
        else:
            questions = Question.query.filter_by(
                category=quiz_category['id']).all()

        # defines a random question generator method
        def get_random_question():
            return questions[random.randint(0, len(questions)-1)]

        # get random question for the next question
        next_question = get_random_question()

        # defines boolean used to check that the question
        # is not a previous question
        found = True

        while found:
            if next_question.id in previous_questions:
                next_question = get_random_question()
            else:
                found = False

        return jsonify({
            'success': True,
            'question': next_question.format(),
        }), 200

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request'
        }), 400

    # Error handler for resource not found (404)
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource not found'
        }), 404

    # Error handler for internal server error (500)
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'internal server error'
        }), 500

    # Error handler for unprocesable entity (422)
    @app.errorhandler(422)
    def unprocesable_entity(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable entity'
        }), 422

    return app
