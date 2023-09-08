import pytest,os

def dump(content):
    with open("local.dump","w",encoding="utf-8") as write_stream:
        write_stream.write(repr(content))

class TestCodeforcesPractice:
    def test_function_execution(arg):
        try:
            os.mkdir("_users")
        except FileExistsError:
            pass
        assert True
    def test_rating_calculate(arg):
        with open("_users/profile_test_user_only_generated.json","w",encoding="utf-8") as write_stream:
            write_stream.write('{"username":"test_user_only","contest_history":[{"problemId":"1A","beat":false,"time":1000000000},{"problemId":"1A","beat":true,"time":1000000002}]}')
        s = os.popen('python ./tools.py --handle test_user_only --show').read()
        assert('496.5' in s)
        assert('Welcome' in s)
        # assert(s=='Welcome,user test_user_only.\n    1 \x1b[30mmath                          \x1b[0m               \x1b[30m  496.5 [############                                                                                        ]\x1b[0m\n')
    def test_problem_predict(arg):
        s = os.popen('python ./tools.py --handle test_user_only --predict 1A').read()
        assert('Welcome' in s)
        assert('5.2' in s)
        assert('1000' in s)
        assert('Accepted' in s)
        # assert(s=='Welcome,user test_user_only.\nrating of problem \x1b[30m1A    \x1b[0m is \x1b[30m1000 \x1b[0m, your accepted rate is 5.2 % ( \x1b[30mmath 10.00%\x1b[0m )\nYou have \x1b[32mAccepted\x1b[0m this problem.\n')
    def test_contest_predict(arg):
        s = os.popen('python ./tools.py --handle test_user_only --predict-contest 1').read()
        assert('Welcome' in s)
        assert('0.0' in s)
        # assert(s=='Welcome,user test_user_only.\nrating of problem \x1b[33m1C    \x1b[0m is \x1b[33m2100 \x1b[0m, your accepted rate is 0.0 % ( \x1b[30mgeometry 0.00%\x1b[0m  \x1b[30mmath 0.00%\x1b[0m )\nrating of problem \x1b[34m1B    \x1b[0m is \x1b[34m1600 \x1b[0m, your accepted rate is 0.1 % ( \x1b[30mimplementation 0.00%\x1b[0m  \x1b[30mmath 0.00%\x1b[0m )\nrating of problem \x1b[30m1A    \x1b[0m is \x1b[30m1000 \x1b[0m, your accepted rate is 5.2 % ( \x1b[30mmath 10.00%\x1b[0m )\nYou have \x1b[32mAccepted\x1b[0m this problem.\n')
    def test_recent(arg):
        s = os.popen('python ./tools.py --handle test_user_only --recent 1').read()
        assert('Welcome' in s)
        assert('2001-09-09, 09:46:40' in s)
        assert('Unaccepted' in s)
        s = os.popen('python ./tools.py --handle test_user_only --recent 2').read()
        assert('Accepted' in s)
        # assert(s=="Welcome,user test_user_only.\ntest_user_only's recent status:\n1970-01-01, 08:00:00 \x1b[30m1A    \x1b[0m \x1b[32mAccepted\x1b[0m\n")

if __name__ == '__main__':
    pytest.main('')
