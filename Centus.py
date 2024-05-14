"""
Centuś
(C) Wojciech Jawień, 2024

Problem:
Given a matrix of weights find a path of a given length that minimizes
the sum of weights on the path.

Solution:
Dwave Ocean Software is used to formulate this task as the
Constraint Satisfaction Problem and solve it on a quantum sampler.
Most of this code lends from Maze problem by Arcondello

For a somewhat similar yet simpler problem, see Reingold EM, Nievergelt J & Deo N,
(1977) Prentice Hall, Englewood Cliffs, NJ
§ 4.5, problem 7.

"""

Length = 5  # start & end tiles not counted

import dwavebinarycsp as csp 
import numpy as np
import re # regular expressions
import sys
from dwave.system.samplers import DWaveSampler
from dwave.system.composites import EmbeddingComposite
import pickle

# timing stuff

import time 

def timing():
    start = time.process_time()
    while True:
        t = time.process_time()
        s,start = start,t
        yield t-s
    
class timer:   
    def __init__(self):
        self.tim = timing()
        self.read()  # first reading is lost in principle
    def read(self):
        return next(self.tim)    



# Sample data

# The original problem was a maximum search with those weights;

'''
weights = np.array([
    [0,6,8,1,7,4,3,4,8,9,9,1],
    [2,7,6,9,4,9,9,5,0,9,0,2],
    [2,8,7,4,7,0,1,9,3,8,2,7],
    [6,4,2,2,0,7,1,6,1,8,1,4],
    [2,1,3,6,1,6,3,6,3,1,8,1],
    [2,7,9,0,2,4,2,4,6,0,9,1],
    [9,0,4,3,8,9,9,4,2,5,1,3],
    [3,5,9,5,0,6,1,9,1,9,6,2],
    [3,0,9,8,9,4,3,4,9,3,1,2],
    [3,8,2,1,8,9,0,1,4,9,1,6]])



weights = np.array([
    [0,6,8,1],
    [2,7,6,9],
    [2,8,7,4]
    ])



weights = np.array([
    [0,6,8],
    [2,7,6],
    [2,8,7]])



weights = np.array([
    [0,6,8,3,1,9,5],
    [2,7,6,4,5,3,8]])
'''


weights = np.array([
    [0,6,8],
    [2,7,6]])






# This converts it to a minimization task, while preserving one-digit weights

weights = 9 - weights

# A few auxillary functions

# Label processing - nearly a verbatim copy of that of Maze

def get_label(row, col, direction):
    """Provides a string that follows a standard format for naming constraint variables in Board.
    Namely, "<row_index>,<column_index><north_or_west_direction>".

    Args:
        row: Integer. Index of the row.
        col: Integer. Index of the column.
        direction: String in the set {'n', 'w', 's', 'e'}.
            'n' indicates north and 'w' indicates west
            's' is for a start and
            'e' is for an end
    """
    return "{row},{col}{direction}".format(**locals())

def sum_to_two_or_zero(*args):
    """Checks to see if the args sum to either 0 or 2. """
    sum_value = sum(args)
    return sum_value in [0, 2]

def just_one(*args):
    """
    Check, if there is one and only one occurence of '1' in the list.
    Intended to verify, if there is just one start and just one end of path.
    """
    sum_value = sum(args)
    return sum_value == 1

def check_length(*args):
    """
    Check, if the path length equals given value
    It appears to be highly ineffective
    """
    sum_value = sum(args)
    return sum_value == Length 

def ToBQM(weights, length):
    board = Board(weights,length)
    return board.get_bqm()

class Board:
    """ Object representing the problem by constraints and penalties """
    def __init__(self,weights, length):
        (self.rows,self.cols) = weights.shape
        self.length = length
        self.csp =  csp.ConstraintSatisfactionProblem(csp.BINARY)

    def _set_borders(self):
            """
            Sets the values of the outer border of the maze;
            prevents a path from forming over the border.
            """
            for j in range(self.cols):
                top_border = get_label(0, j, 'n')
                bottom_border = get_label(self.rows, j, 'n')
                
                try:
                    self.csp.fix_variable(top_border, 0)
                except ValueError:
                    # if not top_border in [self.start, self.end]:
                    raise ValueError

                try:
                    self.csp.fix_variable(bottom_border, 0)
                except ValueError:
                    #if not bottom_border in [self.start, self.end]:
                    raise ValueError
            
            for i in range(self.rows):
                left_border = get_label(i, 0, 'w')
                right_border = get_label(i, self.cols, 'w')

            
                try:
                    self.csp.fix_variable(left_border, 0)
                except ValueError:
                    # if not left_border in [self.start, self.end]:
                    raise ValueError

                try:
                    self.csp.fix_variable(right_border, 0)
                except ValueError:
                    # if not right_border in [self.start, self.end]:
                    raise ValueError


    def _apply_valid_step_constraint(self):
        """
        Applies a sum to either 0 or 2 constraint on each tile of the board.

        Note: This constraint ensures that a tile is either not entered at all (0),
        or is entered and exited (2).

        
        """
        # Grab the four directions of each maze tile and apply two-or-zero constraint.
        # As starts and ends are to be also taken into account, there are in fact
        # as many as 6 direections
        # Also accumulate starts, ends and allitems
        starts,ends = [],[]
        allitems = []
        
        for i in range(self.rows):
            for j in range(self.cols):
                v1,v2 = get_label(i, j, 'n'), get_label(i, j, 'w')
                v3,v4 = get_label(i+1, j, 'n'), get_label(i, j+1, 'w')
                s = get_label(i, j, 's')
                e = get_label(i, j, 'e')
                if s not in starts: starts.append(s)
                if e not in ends: ends.append(e)
                if v1 not in allitems: allitems.append(v1)
                if v2 not in allitems: allitems.append(v2)
                if v3 not in allitems: allitems.append(v3)
                if v4 not in allitems: allitems.append(v4)
                directions = {v1, v2,
                              v3, v4,
                              s,  e
                             }
                print("directions:",directions,end="")
                self.csp.add_constraint(sum_to_two_or_zero, directions)
                print("add constraint timing",T.read())
        # some debugging        
        print(f"starts={starts}\nends={ends}\nallitems={allitems}")
        # store these lists for later
        self.starts, self.ends, self.allitems = starts,ends,allitems
        self.csp.add_constraint(just_one,starts)
        print("add constraint 1 start timing",T.read())
        self.csp.add_constraint(just_one,ends)
        print("add constraint 1 end timing",T.read())
        self.csp.add_constraint(check_length,allitems)
        print("add constraint on length timing",T.read())
        
    def get_bqm(self):
        """ Applies required constraints and returns bpm for solution """
        self._apply_valid_step_constraint()
        self._set_borders()
        # Grab bqm constrained for valid solutions
               
        bqm = csp.stitch(self.csp, max_graph_size=128)

        print("Initial bqm (without cost of tiles)\nBQM 0 =\n",bqm)

        # Edit bqm to favour optimal solutions
        for v in bqm.variables:
            # Ignore auxiliary variables
            if isinstance(v, str) and re.match(r'^aux\d+$', v):
                print("Aux encountered",v)
                continue

            # Add a penalty to every tile of the path, including start/end
            code = re.match(r'^(\d+),(\d+)([senw])$',v)
            if code:
                row, col = int(code[1]), int(code[2])
                penalty = weights[row,col]
                if code[3] in ['se']: penalty *= 2
                elif code[3] == 'n': penalty += weights[row-1,col]
                else: penalty += weights[row,col-1]
                print("Penalty to ",v,"is",penalty)     
                bqm.add_variable(v, penalty)

        return bqm

T=timer()       

bqm = ToBQM(weights,Length)

fil=open('BQM1.dump','bw')
pickle.dump(bqm,fil)
fil.close()

print("timing :",T.read())

sys.tracebacklimit = 1
print('BQM\n',bqm)
raise ValueError("STOP!!!") # prevent execution on sampler

# Submit BQM to a D-Wave sampler
sampler = EmbeddingComposite(DWaveSampler())
result = sampler.sample(bqm,
                        num_reads=1000,
                        chain_strength=2,
                        label="Centus' problem")
print(result)
print(result.first.sample)

path = [k for k, v in result.first.sample.items() if v==1
            and not re.match(r"^aux(\d+)$", k)]
print(path)


    
    

