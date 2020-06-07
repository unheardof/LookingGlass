# Reference: https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/
class InternalError(Exception):
    status_code = 500

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return { 'message': self.message }
