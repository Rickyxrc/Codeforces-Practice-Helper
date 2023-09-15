"""
Codeforces Practice Helper - rickyxrc
MIT licenced
"""

import os
import json
import math
import datetime
import argparse
import requests
from colorama import Fore,Style,just_fix_windows_console

just_fix_windows_console()

# parse argument

try:
    os.mkdir("_users")
except FileExistsError:
    pass

parser = argparse.ArgumentParser(description=
                                 f"Codeforces Practice Helper -\
                                      by {Fore.CYAN}rickyxrc{Style.RESET_ALL}"
                                 ,prog='helper.py')

parser.add_argument("--handle",help="specify user's handle"
                    ,required=True,type=str)
parser.add_argument("--fetch-problem",
                    help="manually fetch the problem",
                    required=False,action='store_true')
parser.add_argument("--count-min",
                    help="specify the minium problem tried to calculate rating",
                    required=False,type=int,default=50)
parser.add_argument("--ignore-labels",
                    help="specify the ignored labels",required=False,type=list,default=[
    "meet-in-the-middle",
    "chinese remainder theorem",
    "expression parsing",
    "2-sat",
    "ternary search",
    "schedules",
    "two pointers"
])
parser.add_argument("--max-rating-delta",
                    help="specify the maximum rating delta for one submission",
                    required=False,type=float,default=200)
parser.add_argument("--initial-rating",
                    help="specify the initial rating",required=False,type=int,default=300)
parser.add_argument("--max-wrong-attempt",
                    help="specify fetch the max wrong attempt",required=False,type=int,default=5)

group = parser.add_mutually_exclusive_group(required=True)

group.add_argument("--show",help="show user's rating graph in command line",action='store_true')
group.add_argument("--show-all",help="show user's rating graph in command line,including uncalculated part.",action='store_true')
group.add_argument("--recent",help="show user's recent status",type=int)
group.add_argument("--show-delta",help="show user's rating delta",action='store_true')
group.add_argument("--predict",help="predict user's perfomance in a single problem",type=str)
group.add_argument("--predict-contest",help="predict user's perfomance in a contest",type=int)
group.add_argument("--suggest",
                   help="suggest some problem in a range of accept probability \
                   (--suggest prob_min:float prob_max:float number:int)",
                   type=float,nargs=3)
group.add_argument("--suggest-show",help="suggest some problem in a range of \
                   accept probability and show tags of them",type=float,nargs=3)
group.add_argument("--suggest-contest",help="suggest some contest in a range of \
                   accept number probability.",type=float,nargs=3)
group.add_argument("--suggest-contest-show",help="suggest some contest in a range of \
                   accept number probability and show tags of them",type=float,nargs=3)
group.add_argument("--fetch",help="fetch the submissions from the user",action='store_true')

arg = parser.parse_args()

# config file

username = arg.handle

profile_json = f"./_users/profile_{username}_generated.json"
ignored_labels = arg.ignore_labels
count_min = arg.count_min
initial_rating = arg.initial_rating
max_wrong_attempt = arg.max_wrong_attempt
max_rating_delta = arg.max_rating_delta

# global temp variables

problem_submited = []
ratings = {}
latest_rating = {}
accepted = {}
tried = {}

# tools function

def predict(now_rating:float,problem_rating:float) -> float:
    """
    elo rating 基础计算公式
    通过现在 rating 和 题目rating 预测通过率
    """
    return 1/(1+math.pow(10,(problem_rating-now_rating)/400))

def update(now_rating:float,problem_rating:float,result:bool) -> float:
    """
    elo rating 基础计算公式
    通过现在 rating 和 题目rating 以及结果更新rating
    """
    global max_rating_delta
    return now_rating + max_rating_delta * (result - predict(now_rating,problem_rating))

def get_col_from_rating(rating:float) -> str:
    """显示 rating 颜色"""
    if rating < 1200:
        return Fore.LIGHTBLACK_EX
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
    return Fore.LIGHTRED_EX

def update_tuple(now:tuple,problem_rating:float,result:bool) -> tuple:
    """
    用 tuple 的格式更新
    """
    return (update(now[0],problem_rating,result),now[1]+1)

def update_tag(problem_id:str,tag:str,result:bool) -> float:
    """通过题目id，题目标签和结果算出rating变化量"""
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
    new_ratings = update_tuple(ratings.get(tag,(initial_rating,0)),problem_rating,result)

    if arg.show_delta:
        delta = round(new_ratings[0]-ratings.get(tag,(initial_rating,(0,0)))[0],1)
        if delta>0:
            prev_str = f"{Fore.GREEN}+"
        else:
            prev_str = f"{Fore.RED}"
        print(f"{get_col_from_rating(ratings.get(tag,(initial_rating,(0,0)))[0])}{tag:30}{Style.RESET_ALL}{prev_str}{delta}{Style.RESET_ALL}")

    ratings[tag] = new_ratings

def display_line(length:int,process:float)->str:
    """显示一行"""
    res = list(' '*length)
    for i in range(int(length*process)):
        res[i] = '#'
    return ''.join(res)

def display(rating:float)->str:
    """显示进度条"""
    return '['+display_line(100,rating/4000)+']'


def fetch_problem():
    """从 Codeforces 拉取处理题目信息"""
    proceed = {}
    contests = {}
    res = requests.get('https://codeforces.com/api/problemset.problems').json()

    with open("problem.json","w",encoding="utf-8") as write_stream:
        write_stream.write(json.dumps(res))

    for result in res['result']['problems']:
        try:
            if result['type'] == 'PROGRAMMING' and \
                not '*special' in result['tags']:
                proceed[str(result['contestId'])+result['index']] = {
                        'rating' : result['rating'],
                        'tags'   : result['tags'],
                        'name'   : result['name']
                    }
                contests[result['contestId']] = contests.get(result['contestId'],[])
                contests[result['contestId']].append(str(result['contestId'])+result['index'])
        except KeyError:
            pass

    with open("contest.json","w",encoding="utf-8") as write_stream:
        write_stream.write(json.dumps(contests))

    with open("problem_proceed.json","w",encoding="utf-8") as write_stream:
        write_stream.write(json.dumps(proceed))

def fetch_profile(codeforces_user_handle:str):
    """从 Codeforces 刷新用户信息"""
    profile_json = f"./_users/profile_{codeforces_user_handle}" \
                        + "_generated.json"
    request_url = "https://codeforces.com/api/user.status?" \
          + f"handle={codeforces_user_handle}&count=10000"
    user_profile_json = requests.get(request_url,timeout=10).json()
    lis = []
    for profile in user_profile_json['result']:
        if profile['verdict'] == 'TESTING':
            print('ignored testing submission',profile)
        try:
            if profile['passedTestCount'] == 0:
                continue
            res = {
                'problemId':str(profile['problem']['contestId'])+profile['problem']['index'],
                'beat':False,
                'time':profile['creationTimeSeconds']
            }
            if profile['verdict'] == 'OK':
                res['beat'] = True
            lis.append(res)
        except KeyError:
            print('ignored',profile)

    with open(profile_json,"w",encoding="utf-8") as write_stream:
        write_stream.write(json.dumps({
            "username" : codeforces_user_handle,
            "contest_history" : lis
            }))
    print(f'total {len(user_profile_json["result"])}')

def print_ratings(colored = True,color_delta = False,show_all = False):
    """
    图形化地输出 rating 并排行
    """
    global latest_rating
    rating_result = sorted(ratings.items(),key = lambda x:x[1],reverse = True)
    mul = 1
    rating_sum = 0
    num = 0
    cnt_valid = 0
    printed_row = 0
    for rating in rating_result:
        if rating[1][1] > count_min:
            mul *= rating[1][0]
            rating_sum += rating[1][0]
            num += rating[1][1]
            cnt_valid += 1
        else:
            if not show_all:
                continue

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

        print(f"{rating[1][1]:5} {pref}{rating[0]:30}{clear} \
              {control}{round(rating[1][0],1):7} {display(rating[1][0])}{clear}")
        printed_row+=1

    if cnt_valid:
        mul = math.pow(mul,1/cnt_valid)
        rating_sum = rating_sum / cnt_valid
        control = ''
        if colored:
            control = get_col_from_rating(mul)
        clear = Style.RESET_ALL
        print(f"\n{control}{num:5} {'rating (geometric mean)':30} \
              {round(mul,1):7}{clear} {display(mul)}")
        printed_row+=2
        if colored:
            control = get_col_from_rating(rating_sum)
        print(f"{control}{num:5} {'rating (average)':30} \
              {round(rating_sum,1):7}{clear} {display(rating_sum)}")
        printed_row+=1
        latest_rating = ratings.copy()

def win_rate(problem_id):
    """通过题目获取胜率，采用几何平均数"""
    ans = 1
    cnt = 0
    problem_object = problems[problem_id]
    for problem in problem_object['tags']:
        if problem in ignored_labels:
            continue
        my_rating = ratings.get(problem,(initial_rating,0))[0]
        ans *= predict(my_rating,problem_object['rating'])
        cnt += 1
    if cnt == 0:
        return 0
    return math.pow(ans,1/cnt)


def print_predict_problem(problemid:str,output_tried:bool) -> None:
    """输出题目的通过率"""
    clear = Style.RESET_ALL
    print(f'rating of problem {get_col_from_rating(problems[problemid]["rating"])}{problemid:6}{clear}' \
            + f' is {get_col_from_rating(problems[problemid]["rating"])}' \
            + f'{str(round(problems[problemid]["rating"],1)):5}{clear}' \
            + f', your accepted rate is {str(round(win_rate(problemid)*100,1)):4}% (',end='')
    for tag in problems[problemid]['tags']:
        if not tag in ignored_labels:
            if ratings.get(tag,(0,0))[0] == 0:
                print(f' {tag} ',end='')
            else:
                print(f' {get_col_from_rating(ratings.get(tag,(arg.initial_rating,0))[0])}{tag} {round(predict(ratings.get(tag,(arg.initial_rating,0))[0],problems[problemid]["rating"]),1)*100:3.2f}%{clear} ',end='')
    print(')')

    if output_tried:
        if accepted.get(problemid,False):
            print('You have '+Fore.GREEN+'Accepted'+Style.RESET_ALL+' this problem.')
        elif tried.get(problemid,False):
            print('You have '+Fore.RED+'Tried'+Style.RESET_ALL+' this problem.')

def suggest_problem(win_rate_min:float,win_rate_max:float,\
                    limit:int=None,show_more:bool=False) -> None:
    """
    推荐通过率在win_rate_min到win_rate_max之间的题目
    用limit限制数量，show_more控制是否显示详细信息
    """
    print(f"suggest these problem for you (accept prob between "\
          + f"{win_rate_min*100:3.2f}% and {win_rate_max*100:3.2f}%)")
    cnt = 0
    for i in problems:
        if i in problem_submited:
            continue
        rate = win_rate(i)
        if win_rate_min <= rate <= win_rate_max:
            if not show_more:
                print(f"{i:6} {rate*100:3.2f}%")
            else:
                print_predict_problem(i,True)
            cnt+=1
            if limit is not None and cnt == limit:
                break

def welcome_message():
    """显示用户欢迎信息，可能会添加更多"""
    print(f"Welcome,user {dat['username']}.")

if arg.fetch_problem:
    fetch_problem()

if not arg.fetch:
    try:
        with open(profile_json,"r",encoding="utf-8") as read_stream:
            dat = json.loads(read_stream.read())
    except FileNotFoundError:
        print(f'{Fore.YELLOW}user profile not found,fetching automatically.\n'
              + f'You might run manually use --fetch few days later.{Style.RESET_ALL}')
        fetch_profile(arg.handle)
        with open(profile_json,"r",encoding="utf-8") as read_stream:
            dat = json.loads(read_stream.read())
    try:
        with open('problem_proceed.json',"r",encoding="utf-8") as read_stream:
            problems = json.loads(read_stream.read())
    except FileNotFoundError:
        print(Fore.YELLOW+'problem_proceed.json not found,fetching automatically.\nYou might run manually use --fetch-problem few days later.'+Style.RESET_ALL)
        fetch_problem()
        print('problem fetched.')
        with open('problem_proceed.json',"r",encoding="utf-8") as read_stream:
            problems = json.loads(read_stream.read())

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

        if accepted.get(record['problemId'],None) is None or\
              (not record['beat'] and tried.get(record['problemId'],0) > max_wrong_attempt):

            if arg.show_delta:
                print_predict_problem(record['problemId'],False)

            for single_tag in problem_tag:
                if single_tag in ignored_labels:
                    continue
                update_tag(record['problemId'],single_tag,record['beat'])

            if record['beat'] is True:
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
    """显示用户最近的刷题情况，使用 limit 限制数量"""
    print(f"{dat['username']}'s recent status:")
    for index,prob in enumerate(reversed(dat['contest_history'])):
        clear = ''
        control = ''
        if prob['beat']:
            res = 'Accepted'
            control = Fore.GREEN
        else:
            res = 'Unaccepted'
            control = Fore.RED
        clear = Style.RESET_ALL

        try:
            col = get_col_from_rating(problems[prob["problemId"]]["rating"])
        except KeyError:
            col = ''

        print(f'{datetime.datetime.strftime(datetime.datetime.fromtimestamp(prob["time"]),"%Y-%m-%d, %H:%M:%S"):20} ' +
              f'{col}{prob["problemId"]:6}{clear} {control}{res}{clear}')

        if limit is not None and index+1 >= limit:
            return

with open("contest.json",encoding="utf-8") as read_stream:
    contest_data = json.loads(read_stream.read())

def print_predict_contest(contestId:str)->None:
    for k in contest_data[str(contestId)]:
        print_predict_problem(k,True)

def suggest_contest(accept_num_min:float,accept_num_max:float,\
                    limit:int=None,show_more:bool=False) -> None:
    tot = 0
    for k in contest_data.keys():
        cnt = 0
        for c in contest_data[k]:
            if accepted.get(c,None) != None:
                cnt = -10000
            cnt += win_rate(c)
        if accept_num_min <= cnt and cnt <= accept_num_max:
            print(f"suggest contest {k} for you,you can accept {round(cnt,1)} problems.")
            if show_more:
                print_predict_contest(k)
                print("")
            tot+=1
            if limit is not None and tot >= limit:
                return

    # print(accept_num_min,accept_num_max,limit)
        
    

if not arg.fetch:
    welcome_message()
if arg.show:
    print_ratings(True,False,False)
if arg.show_all or arg.show_delta:
    print_ratings(True,False,True)
if arg.predict:
    print_predict_problem(arg.predict,True)
if arg.predict_contest:
    print_predict_contest(arg.predict_contest)
if arg.recent:
    show_recent_status(arg.recent)
if arg.suggest:
    suggest_problem(arg.suggest[0],arg.suggest[1],arg.suggest[2],False)
if arg.suggest_show:
    suggest_problem(arg.suggest_show[0],arg.suggest_show[1],arg.suggest_show[2],True)
if arg.fetch:
    fetch_profile(arg.handle)
if arg.suggest_contest:
    suggest_contest(arg.suggest_contest[0],arg.suggest_contest[1],arg.suggest_contest[2])
if arg.suggest_contest_show:
    suggest_contest(arg.suggest_contest_show[0],arg.suggest_contest_show[1],arg.suggest_contest_show[2],True)
