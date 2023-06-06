from random import randint
from math import exp
from time import time
import multiprocessing
from colorama import Fore as F


def extract(path: str):
    lst, n, formula = [], None, []
    with open(path) as cnf:
        lst = list(cnf.read().split('\n'))
        cnf.close()

    for i in range(len(lst)):
        if lst[i][0] == 'p':
            line = lst[i].split(' ')
            n = int(line[2])
            try:
                m = int(line[3])
            except:
                m = int(line[4])
            break

    for j in range(i+1, i+m-1):
        line, intline = lst[j].split(' '), []
        for k in line[:-1]:   # lst[-1] = 0, shows end of line and we dont need it
            try:
                intline.append(int(k))
            except:
                pass
        if intline != []:
            formula.append(intline)

    return [n, formula]


def enhanced_evaluate(formula: list[list[int]], values: str):
    tmp = False

    for i in formula:  # iterate over conjunction parts

        for j in i:   # iterate over the selected disjunction part

            if j < 0:   # extract value of this statement
                tmp = False if values[-j-1] == '1' else True
            else:
                tmp = False if values[j-1] == '0' else True

            if tmp:
                break
        if not tmp:
            return False

    return True


def evaluate(candidate: str, formula: list[list[int]]):
    cnt = 0
    for i in formula:
        for j in i:
            if j < 0:
                tmp = False if candidate[-j-1] == '1' else True
            else:
                tmp = False if candidate[j-1] == '0' else True
            if tmp:
                cnt += 1
                break
    return cnt


# Flip a coin with the given probabilty of being heads (True)
# and return the result
def flip_coin(prob: float = 50.0) -> bool:
    if prob == 0:
        return False
    elif prob == 100:
        return True
    elif not 0 < prob < 100:
        raise ValueError('Probability must be in [0, 100]')

    mx = 100
    while prob != int(prob):
        prob *= 10
        mx *= 10
    return False if randint(1, mx) > prob else True


def give_noise(state: str, num: int):
    idx = randint(0, num-1)
    new_state = state
    x = '0' if new_state[idx] == '1' else '1'
    new_state = new_state[:idx] + x + new_state[idx+1:]
    return new_state


def random_x(num: int):
    state: str = ''
    for _ in range(num):
        state += '1' if flip_coin(50) else '0'
    return state


def simulated_annealing(iterations, temperature, cooling_ratio, num, formula, lock):
    while(True):
        start = time()
        state: str = random_x(num)
        state_worth = evaluate(state, formula)

        for _ in range(iterations):

            new_state = give_noise(state, num)
            new_state_worth = evaluate(new_state, formula)

            if new_state_worth > state_worth:
                state = new_state
                state_worth = new_state_worth

            else:
                difference = state_worth - new_state_worth
                if difference == 0:
                    prob = 0.5
                else:
                    try:
                        prob = exp(- (difference)/temperature)
                    except ZeroDivisionError:
                        prob = 0

                if flip_coin(prob*100):
                    state = new_state
                    state_worth = new_state_worth

            if state_worth == len(formula):
                break

            temperature *= cooling_ratio

        lock.acquire()
        print(F.LIGHTMAGENTA_EX +
              f'\n{multiprocessing.current_process().name} Says:')

        if state_worth < len(formula):
            print(F.LIGHTRED_EX+'Failed on : ', state_worth)
        else:
            print(end=''+F.LIGHTCYAN_EX)
            for i in range(len(state)):
                print((i+1) if state[i] == '1' else -(i+1), end=' ')
            print()
            break
        print('It took', '%.2f' % (time()-start), 'Seconds'+F.RESET)
        lock.release()
        


if __name__ == '__main__':
    file_num = 35
    path75 = f'uf75/uf75-0{file_num}.cnf'
    path100 = f'uf100/uf100-0{file_num}.cnf'
    path125 = f'uf125/uf125-0{file_num}.cnf'
    path = 'input.cnf'
    num, formula = extract(path100)
    cpu_count = multiprocessing.cpu_count()

    difArgs = [
        (10_000, 100, 0.99),  # 0
        (10_000, 100, 0.90),  # 1
        (10_000, 100, 0.80),  # 2
        (10_000, 999, 0.99),   # 3
        (10_000, 999, 0.90),   # 4
        (10_000, 999, 0.80)  # 5
    ]

    start = time()
    procs: list[multiprocessing.Process] = []
    lock = multiprocessing.Lock()
    for i in range(cpu_count if cpu_count < 3 else cpu_count):
        p = multiprocessing.Process(
            target=simulated_annealing, args=difArgs[i % len(difArgs)] + (num, formula, lock), name=f'Process {i}')
        procs.append(p)

    for i in procs:
        i.start()

    flg = False
    while(True):
        if flg:
            for p in procs:
                p.terminate()
            break
        else:
            for p in procs:
                if not p.is_alive():
                    flg = True
                    break

    print(F.LIGHTYELLOW_EX + '\n\nTotal Time Elpased:', '%.3f' %
          (time()-start), 'Seconds' + F.RESET)
