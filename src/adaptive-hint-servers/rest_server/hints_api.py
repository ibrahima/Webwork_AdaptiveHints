import tornado
from tornado.template import Template
from tornado_database import Connection
import getpass
import json
import tornado.ioloop
import tornado.web

# Connect to webwork mysql database
conn = Connection('localhost', 'webwork', user='root', password=getpass.getpass())

class ProcessQuery(tornado.web.RequestHandler):
    def process_query(self, query_template, write_response=True):
        args = self.request.arguments
        for key in self.request.arguments.keys():
            args[key] = args[key][0]
        query_rendered = Template(query_template) \
            .generate(**args)
        if write_response:
            rows = conn.query(query_rendered)
            self.write(json.dumps(rows)) 
        else:
            conn.execute(query_rendered)

# GET /user_problem_hints?
class UserProblemHints(ProcessQuery):

    def get(self):
        ''' For rendering hints in the student page.  

            Sample arguments:
            course="CompoundProblems",
            user_id="melkherj", 
            set_id="compoundProblemExperiments",
            problem_id=2

            Returning: [{"pg_text": "My name is Mr Hint", "pg_id": "b"}] '''
        query_template = '''
            select {{course}}_hint.pg_id, {{course}}_hint.pg_text 
            from {{course}}_assigned_hint, {{course}}_hint 
            where 
                {{course}}_assigned_hint.user_id="{{user_id}}"        AND
                {{course}}_assigned_hint.hint_id={{course}}_hint.id   AND
                {{course}}_hint.set_id="{{set_id}}"                   AND 
                {{course}}_hint.problem_id={{problem_id}}'''
        self.process_query(query_template)
       

class Hint(ProcessQuery):

    def get(self):
        '''  For helping the instructor read hints
            
            Sample arguments:
            course="CompoundProblems"
            hint_id=2

            With return [{"pg_text": "My name is Mr Hint", "pg_id": "b", 
                "problem_id": 2, "set_id": "compoundProblemExperiments"}] '''
        query_template = '''
            select set_id, problem_id, pg_id, pg_text
            from {{course}}_hint 
            where id={{hint_id}} '''
        self.process_query(query_template)

    def post(self):
        ''' For helping the instructor add hints 
            Sample arguments:
            course=course, 
            pg_id="b",
            set_id="compoundProblemExperiments",
            problem_id=2,
            pg_text="What is [`x^2+4x+2`]?"

            With return None '''
        query_template = '''insert into {{course}}_hint 
            (pg_id, problem_id, set_id, pg_text) values
            ("{{pg_id}}", {{problem_id}}, "{{set_id}}", "{{pg_text}}") '''
        self.process_query(query_template, write_response=False)
       
# GET /problem_hints?

class ProblemHints(ProcessQuery):
    def get(self):
        ''' 
            For listing all hints for a problem (for instructors) that could be reused for other students:

            Sample arguments:
            course="CompoundProblems", 
            set_id="compoundProblemExperiments",
            problem_id=2

            Response: [
                {"pg_text": "My name is Mr Hint", "pg_id": "b"}, 
                {"pg_text": "What is [`x^2+4x+2`]?", "pg_id": "b"}, 
                {"pg_text": "some new problem text!", "pg_id": "b"}, 
                {"pg_text": "some new problem text!", "pg_id": "b"}, 
                {"pg_text": "some new problem text!", "pg_id": "b"}, 
                {"pg_text": "More hints for you dear", "pg_id": "b"}
            ]
            '''
        query_template = '''
            select pg_id, pg_text
            from {{course}}_hint 
            where set_id="{{set_id}}" AND problem_id={{problem_id}} ''' 
        self.process_query(query_template)

# GET /problem_seed?
class ProblemSeed(ProcessQuery):
    def get(self):
        ''' 
            To render problems, we need to get the seed from that problem.  

            Sample arguments:
            course="CompoundProblems", 
            set_id="compoundProblemExperiments",
            problem_id=2
            user_id="melkherj"

            Response: 
                [{"problem_seed": 2225}]
            '''
        query_template = '''
            select problem_seed from {{course}}_problem_user 
            where 
                problem_id={{problem_id}} and 
                user_id="{{user_id}}" and 
                set_id="{{set_id}}";
        '''
        self.process_query(query_template)
        
application = tornado.web.Application([
    (r"/user_problem_hints", UserProblemHints),
    (r"/hint", Hint),
    (r"/problem_hints", ProblemHints),
    (r"/problem_seed", ProblemSeed),
])

if __name__ == "__main__":
    application.listen(8420)
    tornado.ioloop.IOLoop.instance().start()

