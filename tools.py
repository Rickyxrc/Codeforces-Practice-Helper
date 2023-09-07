import json,math,datetime,argparse,requests
from colorama import Fore,Style

# parse argument

parser = argparse.ArgumentParser(description="Codeforces Practice Helper - by " + Fore.GREEN + "rickyxrc" + Style.RESET_ALL,prog='helper.py')

parser.add_argument("--handle",help="specify user's handle",required=True,type=str)
parser.add_argument("--fetch-problem",help="manually fetch the problem",required=False,action='store_true')
parser.add_argument("--count-min",help="specify the minium problem tried to calculate rating",required=False,type=str,default=50)
parser.add_argument("--ignore-labels",help="specify the ignored labels",required=False,type=list,default=[
    "meet-in-the-middle",
    "chinese remainder theorem",
    "expression parsing",
    "2-sat",
    "ternary search",
    "schedules"
])
parser.add_argument("--max-rating-delta",help="specify the maximum rating delta for one submission",required=False,type=float,default=200)
parser.add_argument("--initial-rating",help="specify the initial rating",required=False,type=str,default=300)
parser.add_argument("--max-wrong-attempt",help="specify fetch the max wrong attempt",required=False,type=int,default=5)

group = parser.add_mutually_exclusive_group(required=True)

group.add_argument("--show",help="show user's rating graph in command line",action='store_true')
group.add_argument("--recent",help="show user's recent status",type=int)
group.add_argument("--predict",help="predict user's perfomance in a single problem",type=str)
group.add_argument("--predict-contest",help="predict user's perfomance in a contest",type=int)
group.add_argument("--suggest",help="suggest some problem in a range of accept probability (--suggest prob_min:float prob_max:float number:int)",type=float,nargs=3)
group.add_argument("--suggest-show",help="suggest some problem in a range of accept probability and show tags of them",type=float,nargs=3)
group.add_argument("--fetch",help="fetch the submissions from the user",action='store_true')

arg = parser.parse_args()

# config file

username = arg.handle

profile_json = f"./_users/profile_{username}_generated.json"
ignored_labels = arg.ignore_labels
count_min = arg.count_min
initial_rating = arg.initial_rating
max_wrong_attempt = arg.max_wrong_attempt

# global temp variables

problem_submited = []
ratings = {}
latest_rating = {}
accepted = {}
tried = {}

# tools function

def predict(now_rating:float,problem_rating:float) -> float:
    return 1/(1+math.pow(10,(problem_rating-now_rating)/400))

def update(now_rating:float,problem_rating:float,result:bool) -> float:
    global max_rating_delta
    return now_rating + max_rating_delta * (result - predict(now_rating,problem_rating))

def update_tuple(now:tuple,problem_rating:float,result:bool) -> tuple:
    return (update(now[0],problem_rating,result),now[1]+1)

def update_tag(problem_id:str,tag:str,result:bool) -> float:
    global ratings,problems
    try:
        problem_object = problems[problem_id]
    except KeyError:
        print('can\'t get problem '+problem_id+',ignored.')
        return
    try:
        problem_rating = problem_object['rating']
    except KeyError:
        print('problem '+problem_id+'don\'t have rating judged,ignored.')
        return
    pre_rating = ratings.get(tag,(initial_rating,0))[0]
    ratings[tag] = update_tuple(ratings.get(tag,(initial_rating,0)),problem_rating,result)

def display_line(len:int,process:float)->str:
    res = list(' '*len)
    for i in range(int(len*process)):
        res[i] = '#'
    return ''.join(res)

def display(rating:float)->str:
    return '['+display_line(100,rating/4000)+']'

def get_col_from_rating(rating:float) -> str:
    if rating < 1200:
        return Fore.BLACK
    if rating < 1400:
        return Fore.GREEN
    if rating < 1600:
        return Fore.CYAN
    if rating < 1900:
        return Fore.BLUE
    if rating < 2100:
        return Fore.MAGENTA
    if rating < 2400:
        return Fore.YELLOW
    return Fore.RED

def fetch_problem():
    proceed = {}
    contests = {}
    res = requests.get('https://codeforces.com/api/problemset.problems').json()

    with open("problem.json","w") as write_stream:
        write_stream.write(json.dumps(res))

    for r in res['result']['problems']:
        try:
            if r['type'] == 'PROGRAMMING' and not 'interactive' in r['tags'] and not '*special' in r['tags']:
                proceed[str(r['contestId'])+r['index']] = {
                        'rating' : r['rating'],
                        'tags'   : r['tags'],
                        'name'   : r['name']
                    }
                contests[r['contestId']] = contests.get(r['contestId'],[])
                contests[r['contestId']].append(str(r['contestId'])+r['index'])
        except KeyError:
            pass

    with open("contest.json","w") as write_stream:
        write_stream.write(json.dumps(contests))

    with open("problem_proceed.json","w") as write_stream:
        write_stream.write(json.dumps(proceed))

def fetch_profile(codeforces_user_handle:str):
    profile_json = f"./_users/profile_{codeforces_user_handle}_generated.json"
    request_url = f"https://codeforces.com/api/user.status?handle={codeforces_user_handle}&count=10000"
    dat = requests.get(request_url).json()
    lis = []
    for k in dat['result']:
        if k['verdict'] == 'TESTING':
            print('ignored testing submission',k)
            pass
        try:
            if k['passedTestCount'] == 0:
                continue
            res = {
                'problemId':str(k['problem']['contestId'])+k['problem']['index'],
                'beat':False,
                'time':k['creationTimeSeconds']
            }
            if k['verdict'] == 'OK':
                res['beat'] = True
            lis.append(res)
        except KeyError:
            print('ignored',k)

    with open(profile_json,"w") as write_stream:
        write_stream.write(json.dumps({
            "username" : codeforces_user_handle,
            "contest_history" : lis
            }))
    print(f'total {len(dat["result"])}')

def print_ratings(colored = True,color_delta = False):
    global latest_rating
    rating_result = sorted(ratings.items(),key = lambda x:x[1],reverse = True)
    mul = 1
    sum = 0
    num = 0
    cnt_valid = 0
    printed_row = 0
    for rating in rating_result:
        if rating[1][1] > count_min:
            mul *= rating[1][0]
            sum += rating[1][0]
            num += rating[1][1]
            cnt_valid += 1

        control = ''
        clear = ''
        if colored:
            if color_delta:
                if   rating[1][0] > latest_rating.get(rating[0],(initial_rating,0))[0]:
                    control = Fore.GREEN
                elif rating[1][0] < latest_rating.get(rating[0],(initial_rating,0))[0]:
                    control = Fore.RED

            clear = Style.RESET_ALL
        
            pref = get_col_from_rating(rating[1][0])
            
            if not color_delta:
                control = pref

            if control == '' and rating[1][1] < count_min:
                control = Fore.BLACK

        print(f"{rating[1][1]:5} {pref}{rating[0]:30}{clear} {control}{round(rating[1][0],1):7} {display(rating[1][0])}{clear}")
        printed_row+=1

    if cnt_valid:
        mul = math.pow(mul,1/cnt_valid)
        sum = sum / cnt_valid
        control = ''
        if colored:
            control = get_col_from_rating(mul)
        clear = Style.RESET_ALL
        print(f"\n{control}{num:5} {'rating (geometric mean)':30} {round(mul,1):7}{clear} {display(mul)}")
        printed_row+=2
        if colored:
            control = get_col_from_rating(sum)
        print(f"{control}{num:5} {'rating (average)':30} {round(sum,1):7}{clear} {display(sum)}")
        printed_row+=1
        latest_rating = ratings.copy()

def win_rate(problem_id):
    global ignored_labels
    ans = 1
    cnt = 0
    problem_object = problems[problem_id]
    for t in problem_object['tags']:
        if t in ignored_labels:
            continue
        my_rating = ratings.get(t,(initial_rating,0))[0]
        ans *= predict(my_rating,problem_object['rating'])
        cnt += 1
    if cnt == 0:
        return 0
    return math.pow(ans,1/cnt)


def print_predict_problem(problemid:str):
    clear = Style.RESET_ALL
    print(f'rating of problem {get_col_from_rating(problems[problemid]["rating"])}{problemid:6}{clear} is {get_col_from_rating(problems[problemid]["rating"])}{str(round(problems[problemid]["rating"],1)):5}{clear} , your accepted rate is {str(round(win_rate(problemid)*100,1)):4}% (',end='')
    for t in problems[problemid]['tags']:
        if not t in ignored_labels:
            print(f' {get_col_from_rating(ratings.get(t,(arg.initial_rating,0))[0])}{t} {round(predict(ratings.get(t,(arg.initial_rating,0))[0],problems[problemid]["rating"]),1)*100:3.2f}%{clear} ',end='')
    print(')')
    if accepted.get(problemid,False):
        print('You have '+Fore.GREEN+'Accepted'+Style.RESET_ALL+' this problem.')
    elif tried.get(problemid,False):
        print('You have '+Fore.GREEN+'Tried'+Style.RESET_ALL+' this problem.')

def suggest_problem(win_rate_min:float,win_rate_max:float,limit:int=None,show_more:bool=False)->None:
    print(f"suggest these problem for you (accept prob between {win_rate_min*100:3.2f}% and {win_rate_max*100:3.2f}%)")
    cnt = 0
    for i in problems:
        if i in problem_submited:
            continue
        rate = win_rate(i)
        if rate >= win_rate_min and rate <= win_rate_max:
            if not show_more:
                print(f"{i:6} {rate*100:3.2f}%")
            else:
                print_predict_problem(i)
            cnt+=1
            if limit != None and cnt == limit:
                break

def welcome_message():
    print(f"Welcome,user {dat['username']}.")

if arg.fetch_problem:
    fetch_problem()

if not arg.fetch:
    try:
        with open(profile_json,"r") as read_stream:
            dat = json.loads(read_stream.read())
    except FileNotFoundError:
        print(Fore.YELLOW+'user profile not found,fetching automatically.\nYou might run manually use --fetch few days later.'+Style.RESET_ALL)
        fetch_profile(arg.handle)
        with open(profile_json,"r") as read_stream:
            dat = json.loads(read_stream.read())
    try:
        with open('problem_proceed.json',"r") as read_stream:
            problems = json.loads(read_stream.read())
    except FileNotFoundError:
        print(Fore.YELLOW+'problem_proceed.json not found,fetching automatically.\nYou might run manually use --fetch-problem few days later.'+Style.RESET_ALL)
        fetch_problem()
        print('problem fetched.')
        with open('problem_proceed.json',"r") as read_stream:
            problems = json.loads(read_stream.read())

    max_rating_delta = arg.max_rating_delta

    dat['contest_history'].reverse()

    for index,record in enumerate(dat['contest_history']):
        try:
            problem_object = problems[record['problemId']]
        except KeyError:
            continue
        try:
            problem_tag = problem_object['tags']
        except KeyError:
            continue

        if accepted.get(record['problemId'],None) == None or (not record['beat'] and tried.get(record['problemId'],0) > max_wrong_attempt):

            for single_tag in problem_tag:
                if single_tag in ignored_labels:
                    continue
                update_tag(record['problemId'],single_tag,record['beat'])

            if record['beat'] == True:
                accepted[record['problemId']] = 1
            else:
                tried[record['problemId']] = tried.get(record['problemId'],0) + 1

        if not record['problemId'] in problem_submited:
            problem_submited.append(record['problemId'])

    #     for rating in rating_result:
    #        print(f"{rating[0]:30} {rating[1]:04.1f} {display(rating[1])}")
    #     print(f'\n {record["problemId"]:7} {record["beat"]}')

    #     os.system("cls")
    #     print_ratings(True,True)
    #     print(display(4000*index/len(dat['contest_history'])))
    #     ti = datetime.datetime.fromtimestamp(record['time'])
    #     print(f"{datetime.datetime.strftime(ti,'%Y-%m-%d, %H:%M:%S')}")
    #     time.sleep(0.02)
    # os.system("cls")

def show_recent_status(limit:int=None):
    print(f"{dat['username']}'s recent status:")
    for index,prob in enumerate(reversed(dat['contest_history'])):
        clear = ''
        control = ''
        if prob['beat']:
            res = 'Accepted'
        else:
            res = 'Unaccepted'
        clear = Style.RESET_ALL
        if prob['beat']:
            control = Fore.GREEN
        else:
            control = Fore.RED
        ti = datetime.datetime.fromtimestamp(prob['time'])

        try:
            col = get_col_from_rating(problems[prob["problemId"]]["rating"])
        except KeyError:
            col = ''
        
        print(f'{datetime.datetime.strftime(ti,"%Y-%m-%d, %H:%M:%S"):20} {col}{prob["problemId"]:6}{clear} {control}{res}{clear}')
        
        if limit != None and index+1 >= limit:
            return

if not arg.fetch:
    welcome_message()
if arg.show:
    print_ratings()
if arg.predict:
    print_predict_problem(arg.predict)
if arg.predict_contest:
    with open("contest.json") as read_stream:
        for k in json.loads(read_stream.read())[str(arg.predict_contest)]:
            print_predict_problem(k)
if arg.recent:
    show_recent_status(arg.recent)
if arg.suggest:
    suggest_problem(arg.suggest[0],arg.suggest[1],arg.suggest[2],False)
if arg.suggest_show:
    suggest_problem(arg.suggest_show[0],arg.suggest_show[1],arg.suggest_show[2],True)
if arg.fetch:
    fetch_profile(arg.handle)
