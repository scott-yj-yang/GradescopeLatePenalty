# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/02_nbgrader_process_grade.ipynb.

# %% auto 0
__all__ = ['bcolors', 'nbgrader_grade']

# %% ../nbs/api/02_nbgrader_process_grade.ipynb 3
import canvasapi
from canvasapi import Canvas
import numpy as np
import pandas as pd
import json
from datetime import datetime
import yaml
import os
import requests
import nbformat

# %% ../nbs/api/02_nbgrader_process_grade.ipynb 4
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# %% ../nbs/api/02_nbgrader_process_grade.ipynb 5
class nbgrader_grade:
    def __init__(self,
                 credentials_fp="", # credential file path. [Template of the credentials.json](https://github.com/FleischerResearchLab/CanvasGroupy/blob/main/nbs/credentials.json)
                 late_exception_fp="", # late exception yaml file path. [Template of the late_exception.yaml](https://github.com/scott-yj-yang/GradescopeLatePenalty/tree/main/nbs/api/late_exception.yaml)
                 API_URL="https://canvas.ucsd.edu", # the domain name of canvas
                 course_id="", # Course ID, can be found in the course url
                 assignment_id=-1, # assignment id, can be found in the canvas assignment url
                 grades_fp="", # nbgrader csv grades exports file path 
                 verbosity=0, # Controls the verbosity: 0 = Silent, 1 = print all messages
                ):
        "Initialize Canvas Group within a Group Set and its appropriate memberships"
        self.API_URL = API_URL
        self.canvas = None
        self.course = None
        self.users = None
        self.email_to_canvas_id = None
        self.canvas_id_to_email = None
        self.API_KEY = None
        self.verbosity = verbosity
        self.assignment = None
        self.grades = None
        self.late_exception = dict()
        self.grades_by_assignment = dict()
        self.late_days_by_assignment = dict()
        
        # initialize by the input parameter
        if credentials_fp != "":
            self.auth_canvas(credentials_fp)
        if course_id != "":
            self.set_course(course_id)
        if assignment_id != -1:
            self.link_assignment(assignment_id)
        if late_exception_fp != "":
            self.load_late_exception(late_exception_fp)
        if grades_fp != "":
            self.load_grades_csv(grades_fp)
        
    def auth_canvas(self,
                    credentials_fp: str # the Authenticator key generated from canvas
                   ):
        "Authorize the canvas module with API_KEY"
        with open(credentials_fp, "r") as f:
            credentials = json.load(f)
        self.API_KEY = credentials["Canvas Token"]
        self.GITHUB_TOKEN = credentials["GitHub Token"]
        self.canvas = Canvas(self.API_URL, self.API_KEY)
        # test authorization
        _ = self.canvas.get_activity_stream_summary()
        if self.verbosity != 0:
            print(f"{bcolors.OKGREEN}Authorization Successful!{bcolors.ENDC}")
        
    def set_course(self, 
                   course_id: int # the course id of the target course
                  ):
        "Set the target course by the course ID"
        self.course = self.canvas.get_course(course_id)
        if self.verbosity != 0:
            print(f"Course Set: {bcolors.OKGREEN} {self.course.name} {bcolors.ENDC}")
            print(f"Getting List of Users... This might take a while...")
        self.users = list(self.course.get_users(enrollment_type=['student']))
        if self.verbosity != 0:
            print(f"Users Fetch Complete! The course has {bcolors.OKBLUE}{len(self.users)}{bcolors.ENDC} users.")
        self.email_to_canvas_id = {}
        self.canvas_id_to_email = {}
        for u in self.users:
            try:
                self.email_to_canvas_id[u.email.split("@")[0]] = u.id
                self.canvas_id_to_email[u.id] = u.email.split("@")[0]
            except Exception:
                if self.verbosity != 0:
                    print(f"{bcolors.WARNING}Failed to Parse email and id"
                          f" for {bcolors.UNDERLINE}{u.short_name}{bcolors.ENDC}{bcolors.ENDC}")

    def link_assignment(self,
                        assignment_id: int # assignment id, found at the url of assignmnet tab
                       ) -> canvasapi.assignment.Assignment: # target assignment
        "Link the target assignment on canvas"
        assignment = self.course.get_assignment(assignment_id)
        if self.verbosity != 0:
            print(f"Assignment {bcolors.OKGREEN+assignment.name+bcolors.ENDC} Link!")
        self.assignment = assignment
        return assignment
                    
    def load_grades_csv(self,
                        csv_pf:str # csv file path 
                       ):
        "Load nbgrader exported csv file"
        self.grades = pd.read_csv(csv_pf)
        self._parse_assignments()
    
    def load_late_exception(self,
                            yaml_fp:str # yaml file path stores exception student cases
                           ):
        "Load Late Exception File"
        with open(yaml_fp, "r") as f:
            self.late_exception = yaml.safe_load(f)
        
    def _parse_assignments(self):
        "Parse all assignments by assignment name. And calculate late days used."
        if len(self.grades) == 0:
            raise ValueError("grades has not been loaded. Please loaded via self.load_grades_csv")
        assignments = self.grades["assignment"].unique()
        # I am just lazy :-)
        df = self.grades
        for assignment in assignments:
            A = df[df["assignment"] == assignment]
            # filter those who submitted
            A = A[~A["timestamp"].isna()].copy()
            # remove the redundant user with /
            A = A[~A["student_id"].str.contains("/")].copy()
            A = A.set_index("student_id")
            slip_day_used = self._calculate_late_days(A)
            A["slip_day_used"] = slip_day_used
            # store the parsed result
            self.grades_by_assignment[assignment] = A
            self.late_days_by_assignment[assignment] = A["slip_day_used"]
    
    def check_git_user(user_name):
        """Check that github user exists."""

        page = requests.get('https://github.com/' + user_name, timeout=5)
        return nbgrader_grade._check_page(page)


    def check_git_repo(user_name, repo_name):
        """Check that github repository exists (and is public)."""

        page = requests.get('https://github.com/' + user_name + '/' + repo_name, timeout=5)
        return nbgrader_grade._check_page(page)


    def check_git_file(user_name, repo_name, f_name):
        """Check that a particular file in a github repository exists.

        Notes
        -----
        This will only work for public repos, and assumes that the file is on master.
        """

        page = requests.get('https://github.com/' + user_name + '/' \
                            + repo_name + '/blob/master/' + f_name, timeout=5)
        return nbgrader_grade._check_page(page)

    def _check_page(page):
            """Check status of web page.

            Parameters
            ----------
            page : requests.models.Response() object
            Web page object, returned from requests.get().

            Returns
            -------
            boolean
                Whether the web page exists.

            Notes
            -----
            Approach to checking web page status code comes from here.
                http://stackoverflow.com/questions/16778435/python-check-if-website-exists
            """

            if page.status_code < 400:
                return True
            else:
                return False
    
    def grade_prs(student_details):
        """
        Checks if the PRs exist and grades student based on that
        """
        # Change points distribution of each rubric items
        f = open('Pull_Requests.json')
        pr = json.load(f)
        PR_SCORE = 1
        pr_details = {}
        for n_iter in range(1, 10):
            for pulls in pr:
                for pull in pulls:
                    try:
                        text = (pull["title"] + str(pull["body"])).lower()
                    except TypeError:
                        print(pull)
                        print(pull["title"])
                        print(pull["body"])
                    pr_details[pull["user"]["login"]] = pr_details.get(pull["user"]["login"], "") + text
        for student in student_details:
            if len(student_details[student]["github"]) == 0 or student_details[student]["github"] not in pr_details:
                continue
            last_2 = student_details[student]["pid"][-2:]
            if last_2 in pr_details[student_details[student]["github"]]:
                student_details[student]["score"] += PR_SCORE
                return 1
            else:
                print(student, "PR not found", last_2, student_details[student], pr_details[student_details[student]["github"]])
                return 0
    
    def _calculate_late_days(self, df: pd.DataFrame) -> pd.Series:
        # parse the timestamp
        duedate_format = "%Y-%m-%d %H:%M:%S"
        timestamp_format = "%Y-%m-%d %H:%M:%S.%f"
        df["duedate"] = df["duedate"].apply(lambda x: datetime.strptime(x, duedate_format))
        df["timestamp"] = df["timestamp"].apply(lambda x: datetime.strptime(x, timestamp_format))

        # Calculate the time difference between submission and due date
        late_time_delta = (df["timestamp"] - df["duedate"])

        # Add 3-hour tolerance: Convert 3 hours to timedelta for comparison
        three_hours = pd.to_timedelta(3, unit='h')

        # Apply tolerance: Subtract 3 hours from the late time delta
        adjusted_late_time = late_time_delta - three_hours

        # Calculate late days, use ReLU (Rectified Linear Unit) for positive values only
        slip_day_used = adjusted_late_time.apply(lambda x: np.max([np.ceil(x.total_seconds()/60/60/24), 0]))
    
        return slip_day_used
    
    def get_late_days(self,
                      target_assignment:str, # target assignment name. Must in the column of nbgrader assignment csv 
                      student_id:str # student id
                     ) -> int: # late days of the target assignment
        "Calculate the late day of students submission of the target assignment"
        try:
            late_day = self.late_days_by_assignment[target_assignment][student_id]
        except KeyError:
            if self.verbosity != 1:
                print(f"Student {bcolors.WARNING+student_id+bcolors.ENDC} did "
                      f"not submit {bcolors.WARNING+target_assignment+bcolors.ENDC}")
            late_day = 0
        return late_day
        
    def calculate_credit_balance(self,
                                 passed_assignments:[str], # list of passed assignments name. Must in the column of `assignment`.
                                 student_id:str, # target student
                                 default_credit = 5 # default total number of allowed late days
                                ) -> int: # late credit balance of the target student
        "Calculate the balance of late hours from the nbgrader file"
        # if student is in the late exception, use the new number
        if student_id in self.late_exception:
            default_credit = self.late_exception[student_id]["allowed_late_days"]
        for passed in passed_assignments:
            late_days = self.get_late_days(passed, student_id)
            if late_days <= default_credit:
                # means this passed assignment did not get penalty
                default_credit -= self.get_late_days(passed, student_id)
        return default_credit
    
    def _post_grade(self,
                   student_id: int, # canvas student id of student. found in self.email_to_canvas_id
                   grade: float, # grade of that assignment
                   text_comment="", # text comment of the submission. Can feed
                  ) -> canvasapi.submission.Submission: # created submission
        "Post grade and comment to canvas to the target assignment"
        submission = self.assignment.get_submission(student_id)
        if grade is not None:
            edited = submission.edit(
                submission={
                    'posted_grade': grade
                }, comment={
                    'text_comment': text_comment
                }
            )
        else:
            edited = submission.edit(
                comment={
                    'text_comment': text_comment
                }
            )
        if self.verbosity != 0:
            print(f"Grade for {bcolors.OKCYAN}{self.canvas_id_to_email[student_id]}{bcolors.ENDC} Posted!")
        return edited
    
    def post_to_canvas(self,
                       target_assignment:str, # target assignment name to grab the late time. Must in the column of nbgrader assignment csv 
                       passed_assignments:[str], # list of passed assignment. Must in the column of nbgrader assignment csv
                       post=True, # for testing purposes. Can hault the post operation
                       A_1 = False, # Set True if grading A1 for COGS108
                       git = False, # Set True if grading git part for A1, COGS108
                       Quarter = "" # Set the quarter, for example, Fa23, Wi24, etc.
                      ):
        "Post grade to canvas with late penalty."
        if self.grades is None:
            raise ValueError("Nbgrader CSV has not been loaded. Please set it via self.load_grades_csv")
            
        # Load the GitHub scores if A_1 is True
        student_details = None
        
        if git:
            try:
                f = open('Pull_Requests.json')
                print('Pull Requests opened.')
            except FileNotFoundError:
                pr_link = "https://api.github.com/repos/COGS108/MyFirstPullRequest/pulls?state=all&per_page=100&page="
                pull_requests = []
                for n_iter in range(1, 10):
                    r = requests.get(pr_link + str(n_iter))
                    print(len(r.text))
                    pulls = json.loads(r.text)
                    pull_requests.append(pulls)

                with open("Pull_Requests.json", 'w') as json_file:
                    json.dump(pull_requests, json_file)

                print("Pull Requests fetched and saved.")
        
        for student_id, row in self.grades_by_assignment[target_assignment].iterrows():
            penalty = False
            # fetch useful information
            balance = self.calculate_credit_balance(passed_assignments, student_id)
            late_days = self.get_late_days(target_assignment, student_id)
            score = row["raw_score"]
            
            message = f"{target_assignment}: \n"
            
            if A_1:
                #Initialize scores
                user_score = 0
                repo_score = 0
                file_score = 0
                pr_score = 0
                
                #read students' submissions and fetch Github ID:
                home_dir = os.path.expanduser("~")
                graded_dir = os.path.join(home_dir, "autograded")
                A1_dir = os.path.join(graded_dir, student_id, f"A1_COGS108_{Quarter}")
                try:
                    for file in os.listdir(A1_dir):
                        if file.endswith(".ipynb") and "A1" in file:
                            file_path = os.path.join(A1_dir, file)
                except FileNotFoundError:
                    print(f"{student_id} does not have a submission for A1, skipped to the next student")

                student_details = {}

                nb = nbformat.read(file_path, as_version=4)
                subs=['PID','github_username']
                for cells in nb.cells:
                    try:
                        if cells['metadata']['nbgrader']['grade_id'] == 'cell-784114344a572182':
                            cell = cells
                            break
                    except KeyError:
                        continue
                
                test_list = cell['source'].split('\n')
                res = [i for i in test_list if any(substring in i for substring in subs)]
                print(res)
                if(len(res)!=0):
                    PID_string = [i for i in res if all(substring in i for substring in ['PID','='])] 
                    github_string = [i for i in res if all(substring in i for substring in ['github_username','='])]
                    if(len(PID_string)!=0 and len(github_string)!=0):
                        PID = (PID_string[-1].split('='))[-1].strip().strip("'").strip('"') 
                        github_username = (github_string[-1].split('='))[-1].strip().strip("'").strip('"')
                        #print(student_id, PID, github_username)
                        student_details[student_id] = {"pid": PID, "github": github_username, "score": 0}

                #print(student_details)

                try:
                    if len(student_details[student_id]["github"]) == 0:
                        print('GitHub ID does not exist')
                        pass

                    #User exists:
                    if nbgrader_grade.check_git_user(student_details[student_id]["github"]):
                        student_details[student_id]["score"] += 0.5
                        #print(student_details)
                        user_score = 0.5

                    #Repo exists:
                    if nbgrader_grade.check_git_repo(student_details[student_id]["github"], "COGS108_repo"):
                        student_details[student_id]["score"] += 0.5
                        #print(student_details)
                        repo_score = 0.5

                    #Files exist:
                    is_gitignore = nbgrader_grade.check_git_file(student_details[student_id]["github"], "COGS108_repo", ".gitignore")
                    is_readme = nbgrader_grade.check_git_file(student_details[student_id]["github"], "COGS108_repo", "README")
                    is_readme = is_readme or nbgrader_grade.check_git_file(student_details[student_id]["github"], "COGS108_repo", "README.txt")
                    is_readme = is_readme or nbgrader_grade.check_git_file(student_details[student_id]["github"], "COGS108_repo", "README.md")
                    if is_gitignore and is_readme:
                        student_details[student_id]["score"] += 0.5
                        #print(student_details)
                        file_score = 0.5

                    #Pull requests:
                    pr_score = nbgrader_grade.grade_prs(student_details)

                    score += student_details[student_id]["score"]

                    message += f"user_exists_score: {user_score},\n"
                    message += f"repo_exists_score: {repo_score},\n"
                    message += f"files_exist_score: {file_score},\n"
                    message += f"pull_request_score: {pr_score}.\n"

                # build message for each student
                except KeyError:
                    print('User does not exist, skipped grading git.')
                    message += f"No information provided in assignment, 0 automatically assigned for git part.\n"
                    pass
            
            if late_days > 0:
                # means late submission. Check remaining slip day
                message += f"Late Submission: {int(late_days)} Days Late\n"
                if balance - late_days < 0:
                    message += "Insufficient Slip Credit. 25% late penalty applied\n"
                    score = round(score * 0.75, 4)
                    penalty = True
                else:
                    message += "Slip Credit Used. No late penalty applied\n"
            else:
                message += "Submitted intime\n"
            if not penalty:
                # if student did not get penalized and use the slip day
                balance_after = balance - late_days
            else:
                # if the student did get penalized and did not use the slip day
                balance_after = balance
            message += f"Remaining Slip Credit: {int(balance_after)} Days"
            if post:
                try:
                    canvas_student_id = self.email_to_canvas_id[student_id]
                    self._post_grade(grade=score, student_id=canvas_student_id, text_comment=message)
                    if self.verbosity != 0:
                        print(f"The message for {bcolors.OKCYAN+student_id+bcolors.ENDC} "
                              f"is: \n{bcolors.OKGREEN+message+bcolors.ENDC}\n"
                              f"The score is {bcolors.OKGREEN}{score}{bcolors.ENDC}\n\n"
                         )
                except Exception as e:
                    print(f"Studnet: {bcolors.WARNING+student_id+bcolors.ENDC} Not found on canvas. \n"
                          f"Maybe Testing Account or Dropped Student")
                    print(e)
                    pass
            else:
                print(f"{bcolors.WARNING}Post Disabled{bcolors.ENDC}\n"
                      f"The message for {bcolors.OKCYAN+student_id+bcolors.ENDC} "
                      f"is: \n{bcolors.OKGREEN+message+bcolors.ENDC}\n"
                      f"The score is {bcolors.OKGREEN}{score}{bcolors.ENDC}\n\n"
                     )
        
