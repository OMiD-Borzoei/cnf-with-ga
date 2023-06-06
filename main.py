from random import randint  # not Optimom
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
            break

    for j in range(i+1, len(lst)):
        line, intline = lst[j].split(' '), []
        for k in line[:-1]:   # lst[-1] = 0, shows end of line and we dont need it
            try:
                intline.append(int(k))
            except:
                pass
        if intline != []:
            formula.append(intline)

    return [n, formula]


def enhanced_evaluate(formula: list[list[int]], values: list[int]):
    tmp = False

    for i in formula:  # iterate over conjunction parts

        for j in i:   # iterate over the selected disjunction part

            if j < 0:   # extract value of this statement
                tmp = not values[-j-1]
            else:
                tmp = values[j-1]

             # result of the disjunction is true even if one of the statements inside of it is true, thus there's no point in iterating further
            if tmp:
                break

        # result of the conjunction is false, even if one of the statements iniside of it is false, thus there's no point in iterating further
        if not tmp:
            return False
    # We reach the below line if and only if the result of all conjunction statements was true
    return True


# Flip a coin with the given probabilty of being heads (True)
# and return the result
def flip_coin(prob: float = 50.0) -> bool:
    mx = 100
    while prob != int(prob):
        prob *= 10
        mx *= 10
    return False if randint(1, mx) > prob else True


class Creature():
    def __init__(self, gen: list[bool], worth: int) -> None:
        self.gen = gen
        self.worth = worth

    def __eq__(self, __value: object) -> bool:
        if type(__value) == Creature:
            return __value.gen == self.gen and __value.worth == self.worth
        return False


class GeneticAlgorithm():

    def __init__(self, n, formula, mu=100, population: list[Creature] = []) -> None:
        self.n = n
        self.formula = formula
        self.mu = mu
        self.population = population

    def init_population(self,) -> None:
        self.population = []
        x = [False]*self.n
        self.population.append(Creature(x, self.evaluate(x)))
        for _ in range(self.mu-2):
            inner = []
            for _ in range(self.n):
                inner.append(flip_coin(50))
            self.population.append(Creature(inner, self.evaluate(inner)))
        x = [True]*self.n
        self.population.append(Creature(x, self.evaluate(x)))

    def breed(self, mom: Creature, dad: Creature, mutation_probability: float, max_mutated_genes: int) -> Creature:
        cut_point = randint(0, self.n-1)

        if flip_coin(50):  # 50% chance if mom comes first
            child = mom.gen[:cut_point] + dad.gen[cut_point:]
        else:
            child = dad.gen[:cut_point] + mom.gen[cut_point:]

        if flip_coin(mutation_probability):
            if max_mutated_genes == 1:
                mutated_genes = 1
            else:
                mutated_genes = self.pick(
                    ln=max_mutated_genes, reverse=True) + 1  # reverse reward_based
            for _ in range(mutated_genes):
                idx = randint(0, self.n-1)
                child[idx] = not child[idx]

        return Creature(child, self.evaluate(child))

    def pick(self, reverse=False, alg='reward_based', ln=None) -> int:  # returns the idx of a creature
        if ln is None:
            ln = self.mu
        x = randint(1, (ln*(ln+1))/2)
        idx, tmp = 0, 0
        while tmp < x:
            idx += 1
            tmp = (idx*(idx+1))/2
        return idx - 1 if not reverse else ln - idx

    def make_new_generation(self, breed_probability: int, mutation_probability: float, max_mutated_genes: int) -> list[list[bool]]:
        new_gen = []
        for _ in range(self.mu):
            # Let's flip the coin
            if flip_coin(breed_probability):

                mom_idx = self.pick(alg='reward_based')
                dad_idx = self.pick(alg='reward_based')

                mom, dad = self.population[mom_idx], self.population[dad_idx]

                # Now that mom and that are picked, let's make a baby :)
                child = self.breed(
                    mom, dad, mutation_probability, max_mutated_genes)

                new_gen.append(child)

        # Return all the babies
        return new_gen

    def let_there_be_carnage(self,) -> None:
        # Kill as long as the world is over populated:
        while len(self.population) > self.mu:
            # Pick a creature using reverse reward_base (give more chance to the weak)
            weak_idx = self.pick(reverse=True)
            self.population.pop(weak_idx)  # Kill them in cold blood :)

    def evolve(self, mutation_probability, breed_probability, survivor_choose_method, max_mutated_genes, max_generations):
        survivor_choose_methods = ['child_only', 'child_and_parent']
        # raise error if the passed argument is invalid
        self.check_method(survivor_choose_method, survivor_choose_methods)

        self.init_population()  # Fill the world with a complete random population

        for _ in range(max_generations):  # evolve for a limited number of generations

            new_gen = self.make_new_generation(
                breed_probability, mutation_probability, max_mutated_genes)  # extract babies

            # (mu+lamda)
            if survivor_choose_method == survivor_choose_methods[1]:
                self.population += new_gen
            else:  # (mu, mu)
                self.population = new_gen

            # sort the world, higher indices are more worthy
            self.population.sort(key=lambda e: e.worth)
            # kill:
            self.let_there_be_carnage()

            # if the worthiest creature has the maximum available worth, return its genome:
            # it means we've reached the highest mountain in the landscape and we don't need to continue evolving
            if self.population[-1].worth >= len(self.formula):
                return self.population[-1].gen

        # We've failed this time and didn't reach the highest mountain in landscape
        return None

    # calls the evolve function over and over until it reaches the answer
    def solve(self, mutation_probability=90, max_mutated_genes=1, breed_probability=95, survivor_choose_method='child_and_parent',  max_generations=1000, lock=None):
        i = 0
        while(True):
            i += 1
            x = time()
            # call the solve function and wait
            ans = self.evolve(mutation_probability, breed_probability,
                              survivor_choose_method, max_mutated_genes, max_generations)
            y = time()

            # For multiprocessed solving we need to lock the terminal so that other processes don't ruin what we are goin to write in it
            if lock:
                lock.acquire()
                # we also need to specify which process is writing in the terminal:
                print(F.LIGHTMAGENTA_EX +
                      f'\n{multiprocessing.current_process().name}', 'Says:'+F.RESET)

            # If ans is not None, it means that the evolve function has succeded and found the answer
            if ans:
                print(F.LIGHTGREEN_EX+'Try', i,
                      'Ended in Success\nIt took %.2f' % (y-x), 'Seconds', F.LIGHTCYAN_EX)
                for j in range(len(ans)):
                    print((j+1) if ans[j] else -(j+1), end=' ')
                print()
                if lock:
                    lock.release()
                break

            # If ans is None, we need to call the evolve funciton again
            else:
                print(F.LIGHTRED_EX+'Try', i, 'Ended in Failure\nIt took %.2f' %
                      (y-x), 'Seconds'+F.RESET + '\nFound max worth of', self.population[-1].worth)

            if lock:
                lock.release()

    def evaluate(self, candidate: list[bool]):
        cnt, tmp = 0, False
        for i in self.formula:
            for j in i:
                if j < 0:
                    tmp = not candidate[-j-1]
                else:
                    tmp = candidate[j-1]
                if tmp:
                    cnt += 1
                    break
        return cnt

    @staticmethod
    def check_method(given, reference):
        if given not in reference:
            raise ValueError(f'{given} is not in {reference}')



if __name__ == '__main__':
    file_num = 5
    path75 = f'uf75/uf75-0{file_num}.cnf'
    path100 = f'uf100/uf100-0{file_num}.cnf'
    path125 = f'uf125/uf125-0{file_num}.cnf'
    path = 'input.cnf'
    num, formula = extract(path)
    
    cpu_count = multiprocessing.cpu_count() # Physical Cores
    
    difArgs = [
        (99, 1, 99, 'child_and_parent', 1_000, 26),  # 0
        (98, 1, 99, 'child_and_parent', 1_200, 25),  # 1
        (97, 1, 99, 'child_and_parent', 1_400, 24),  # 2
        (96, 1, 99, 'child_and_parent', 1_600, 23),  # 3
        (95, 1, 99, 'child_and_parent', 1_800, 22),  # 4
        (94, 1, 99, 'child_and_parent', 2_000, 21),  # 5
        (93, 1, 99, 'child_and_parent', 2_200, 20),  # 6
        (92, 1, 99, 'child_and_parent', 1_000, 20),  # 7
    ]

    start = time()
    procs: list[multiprocessing.Process] = []
    lock = multiprocessing.Lock()
    
    for i in range(cpu_count if cpu_count < 3 else cpu_count-1):
        ga = GeneticAlgorithm(num, formula, mu=difArgs[i % len(difArgs)][-1])
        p = multiprocessing.Process(
            target=ga.solve, args=difArgs[i % len(difArgs)][:-1] + (lock,), name=f'Process {i}')
        procs.append(p)
        p.start()       # start the process

    flg = False
    # if even one of the processes finished their work, terminate all other processes and exit
    while(True):  
        # If some Process finished:          
        if flg:
            # terminate everyone
            for p in multiprocessing.active_children():
                p.terminate()
            break   # get out of inf loop
        
        else:
            # check:
            for p in procs:
                if not p.is_alive(): # if this process has finished his work, raise the flag   
                    flg = True
                    break            # No need to check other processes 
    end = time()
    print(F.LIGHTYELLOW_EX + '\n\nTotal Time Elpased:', '%.3f' %
          (end-start), 'Seconds' + F.RESET)

