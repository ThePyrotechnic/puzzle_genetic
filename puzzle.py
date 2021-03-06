from collections import defaultdict
from copy import deepcopy
from io import StringIO
import random
from typing import List, Dict

import attr


SIDES = {
    1: 'R0',
    2: 'R1',
    3: 'G0',
    4: 'G1',
    5: 'B0',
    6: 'B1',
    7: 'Y0',
    8: 'Y1'
}


def get_pair(side: int) -> int:
    return side - 1 if side % 2 == 0 else side + 1


class Puzzle:
    def __init__(self, x: int = 3, y: int = 3):
        self.x: int = x
        self.y: int = y
        self.pieces: List[List['Piece']] = [[0] * x for _ in range(y)]

    def __str__(self):
        out = StringIO()
        max_num_width = len(str(self.x * self.y))

        for x_ in range(self.x):
            print(f'+-------{"-" * max_num_width}' * self.x, end='', file=out)
            print('+', file=out)
            for y_ in range(self.y):
                num_width = len(str(self.pieces[x_][y_].num))
                print(f'|{self.pieces[x_][y_].num}{" " * (max_num_width - num_width)}  {SIDES[self.pieces[x_][y_].top]}   ', end='', file=out)
            print('|', file=out)
            for y_ in range(self.y):
                print(f'|{SIDES[self.pieces[x_][y_].left]}{" " * max_num_width}   {SIDES[self.pieces[x_][y_].right]}', end='', file=out)
            print('|', file=out)
            for y_ in range(self.y):
                print(f'|{" " * max_num_width}  {SIDES[self.pieces[x_][y_].bottom]}   ', end='', file=out)
            print('|', file=out)
        print(f'+-------{"-" * max_num_width}' * self.x, end='', file=out)
        print('+', file=out)

        out_str = out.getvalue()
        out.close()

        return out_str

    def shuffle(self):
        all_pieces = [piece for row in self.pieces for piece in row]
        random.shuffle(all_pieces)

        for x_ in range(self.x):
            self.pieces[x_] = []
            for _ in range(self.y):
                piece = all_pieces.pop()
                [piece.rotate() for _ in range(random.randint(0, 3))]
                self.pieces[x_].append(piece)

    def distances(self) -> Dict[int, List[Dict]]:
        distances = defaultdict(list)
        for r1 in self.pieces:
            for piece in r1:
                for r2 in self.pieces:
                    for other in r2:
                        distances[piece.num].append({'num': other.num, 'distance': piece.distance(other), 'ref': other})
        return distances

    @classmethod
    def random_solvable(cls, x: int = 3, y: int = 3) -> 'Puzzle':
        puzzle = Puzzle(x, y)
        for x_ in range(x):
            for y_ in range(y):
                puzzle.pieces[x_][y_] = Piece(
                    top=get_pair(puzzle.pieces[x_ - 1][y_].bottom) if x_ - 1 >= 0 else random.choice(list(SIDES.keys())),
                    right=random.choice(list(SIDES.keys())),
                    bottom=random.choice(list(SIDES.keys())),
                    left=get_pair(puzzle.pieces[x_][y_ - 1].right) if y_ - 1 >= 0 else random.choice(list(SIDES.keys())),
                    num=x * x_ + y_
                )
        return puzzle

    def fitness(self):
        fitness = 0
        for x_ in range(self.x):
            for y_ in range(self.y):
                if y_ + 1 < self.y and get_pair(self.pieces[x_][y_].right) != self.pieces[x_][y_+1].left:
                    fitness += 1
                if x_ + 1 < self.x and get_pair(self.pieces[x_][y_].bottom) != self.pieces[x_+1][y_].top:
                    fitness += 1
        return fitness


@attr.s
class Piece:
    top: int = attr.ib()
    right: int = attr.ib()
    bottom: int = attr.ib()
    left: int = attr.ib()
    num: int = attr.ib()

    def rotate(self):
        top = self.top
        right = self.right
        bottom = self.bottom
        left = self.left
        self.top = left
        self.right = top
        self.bottom = right
        self.left = bottom

    def distance(self, other: 'Piece'):
        distance = 0
        if get_pair(self.left) != other.right:
            distance += 1
        if get_pair(self.right) != other.left:
            distance += 1
        if get_pair(self.top) != other.bottom:
            distance += 1
        if get_pair(self.bottom) != other.top:
            distance += 1

        return distance

    def __eq__(self, other):
        return self.num == other.num and self.top == other.top and self.right == other.right and self.bottom == other.bottom and self.left == other.left


def population(puzzle: Puzzle, count: int) -> List[Puzzle]:
    pop = [deepcopy(puzzle) for _ in range(count)]
    [p.shuffle() for p in pop]
    return pop


def grade(pop: List[Puzzle]) -> float:
    return sum([puzzle.fitness() for puzzle in pop]) / len(pop)


def fill_gaps(child: Puzzle, distances: Dict[int, List[Dict]]):
    used_piece_nums = set()
    for r1 in child.pieces:
        for piece in r1:
            if piece != 0:
                used_piece_nums.add(piece.num)

    for x_ in range(child.x):
        for y_ in range(child.y):
            if child.pieces[x_][y_] == 0:
                possible_pieces = None
                if y_ + 1 < child.y and child.pieces[x_][y_+1] != 0:
                    possible_pieces = [d for d in distances[child.pieces[x_][y_+1].num] if d['num'] not in used_piece_nums]
                elif x_ + 1 < child.x and child.pieces[x_+1][y_] != 0:
                    possible_pieces = [d for d in distances[child.pieces[x_+1][y_].num] if d['num'] not in used_piece_nums]
                elif x_ - 1 >= 0 and child.pieces[x_-1][y_] != 0:
                    possible_pieces = [d for d in distances[child.pieces[x_-1][y_].num] if d['num'] not in used_piece_nums]
                elif y_ - 1 >= 0 and child.pieces[x_][y_-1] != 0:
                    possible_pieces = [d for d in distances[child.pieces[x_][y_-1].num] if d['num'] not in used_piece_nums]
                else:
                    random_piece = deepcopy(random.choice([d for d in distances[0] if d['num'] not in used_piece_nums])['ref'])
                    used_piece_nums.add(random_piece.num)
                    child.pieces[x_][y_] = random_piece
                if possible_pieces:
                    possible_pieces.sort(key=lambda x: x['distance'])
                    used_piece_nums.add(possible_pieces[0]['num'])
                    child.pieces[x_][y_] = deepcopy(possible_pieces[0]['ref'])


def crossover(mother: Puzzle, father: Puzzle, distances: Dict[int, List[Dict]]):
    child = Puzzle(x=mother.x, y=mother.y)

    for x_ in range(child.x):
        for y_ in range(child.y):
            if mother.pieces[x_][y_] == father.pieces[x_][y_]:
                child.pieces[x_][y_] = mother.pieces[x_][y_]

    fill_gaps(child, distances)

    return child


def evolve(pop: List[Puzzle], distances: Dict[int, List[Dict]], retain: float = 0.2, random_select_chance: float = 0.05, mutate_chance: float = 0.05):
    pop.sort(key=lambda p: p.fitness())
    cutoff = int(len(pop) * retain)
    new_parents = pop[:cutoff]

    for p in pop[cutoff:]:
        if random_select_chance > random.random():
            new_parents.append(p)

    for p in new_parents:
        if mutate_chance > random.random():
            # p.shuffle()
            r_x = random.randint(0, p.x - 1)
            r_y = random.randint(0, p.y - 1)
            [p.pieces[r_x][r_y].rotate() for _ in range(random.randint(0, 3))]
            p.pieces[r_x][r_y] = p.pieces[random.randint(0, p.x - 1)][random.randint(0, p.y - 1)]

    desired_size = len(pop) - len(new_parents)
    children = []
    while len(children) < desired_size:
        father = random.choice(new_parents)
        mother = random.choice(new_parents)
        if mother != father:
            child = crossover(mother, father, distances)
            children.append(child)
    new_parents.extend(children)
    return new_parents


def main():
    puzzle = Puzzle.random_solvable(x=3, y=3)
    solution = str(puzzle)
    puzzle.shuffle()
    distances = puzzle.distances()

    pop = population(puzzle, 1000)

    print(f'Start. Fitness: {puzzle.fitness()}')
    print(puzzle)

    sum_of_grades = 0
    last_avg = 100
    for gen in range(10000):
        pop = evolve(pop, distances, retain=0.4, random_select_chance=0.05, mutate_chance=0.01)
        cur_grade = grade(pop)
        print(f'Gen {gen + 1}: Grade: {cur_grade}')
        sum_of_grades += cur_grade
        if (gen + 1) % 50 == 0:
            avg = sum_of_grades/(gen + 1)
            print(f'Average grade difference: {last_avg - avg}')
            if last_avg - avg < 0.1:
                print('Stopping early because grade improvement of last 50 generations has slowed below threshold')
                break
            last_avg = avg
    best = min(pop, key=lambda p: p.fitness())
    print(f'End. Fitness: {best.fitness()}')
    print(best)

    print('Correct solution:')
    print(solution)


if __name__ == '__main__':
    main()
