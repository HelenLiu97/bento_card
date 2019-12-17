from flask import Flask
import time
from concurrent.futures import ThreadPoolExecutor
from time import sleep

executor = ThreadPoolExecutor(1)

app = Flask(__name__)


@app.route('/jobs')
def run_jobs():
    executor.submit(some_long_task1)
    executor.submit(some_long_task2, 'hello', 123)
    executor.submit(some_long_task3, 'hello', 456)
    executor.submit(some_long_task4, 'hello', 789)
    return 'Two jobs was launched in background!'


def some_long_task1():
    print("Task #1 started!")
    sleep(10)
    print("Task #1 is done!")


def some_long_task2(arg1, arg2):
    print("Task #2 started with args: %s %s!" % (arg1, arg2))
    sleep(5)
    print("Task #2 is done!")

def some_long_task3(arg1, arg2):
    print("Task #2 started with args: %s %s!" % (arg1, arg2))
    sleep(5)
    print("Task #2 is done!")

def some_long_task4(arg1, arg2):
        print("Task #2 started with args: %s %s!" % (arg1, arg2))
        sleep(5)
        print("Task #2 is done!")



if __name__ == '__main__':
    app.run()
