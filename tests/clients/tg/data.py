GET_ME = {'ok': True,
          'result': {'id': 987654321, 'is_bot': True, 'first_name': 'glktest', 'username': 'glktestbot',
                     'can_join_groups': True, 'can_read_all_group_messages': False, 'supports_inline_queries': False}}

GET_UPDATES = {'ok': True, 'result': [{
    'update_id': 503972234,
    'message': {
        'message_id': 1,
        'from': {'id': 123456789, 'is_bot': False, 'first_name': 'Alexander', 'last_name': 'Goliak',
                 'username': 'alGLK', 'language_code': 'en'},
        'chat': {'id': 123456789, 'first_name': 'Alexander', 'last_name': 'Goliak', 'username': 'alGLK',
                 'type': 'private'},
        'date': 1634815235,
        'text': '/start',
        'entities': [{'offset': 0, 'length': 6, 'type': 'bot_command'}]
    }}
]}
GET_OFFSET_UPDATES = {'ok': True, 'result': []}

SEND_MESSAGE = {'ok': True, 'result': {
    'message_id': 13, 'from': {'id': 987654321, 'is_bot': True, 'first_name': 'glktest', 'username': 'glktestbot'},
    'chat': {'id': 123456789, 'first_name': 'Alexander', 'last_name': 'Goliak', 'username': 'alGLK',
             'type': 'private'}, 'date': 1634901940, 'text': 'hello'
}}
