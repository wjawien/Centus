"""
Centuś classic
(C) Wojciech Jawień, 2024

Problem:
Given a matrix of weights ("board") find a path of a given length that minimizes
the sum of weights on the path.

Solution:
Dynamic programming was used.


For a somewhat similar yet simpler problem, see Reingold EM, Nievergelt J & Deo N,
(1977) Prentice Hall, Englewood Cliffs, NJ
§ 4.5, problem 7.

"""

import numpy as np
import time
from random import randrange

Length = 25
infinity = 32768 # for instance...

lowcost = infinity
solution = set()

# ancillary functions

def timing():
    start = time.process_time()
    while True:
        t = time.process_time()
        s,start = start,t
        yield t-s
    
class timer:   
    def __init__(self):
        self.tim = timing()
        self.odczyt()  # first reading is lost, in principle
    def odczyt(self):
        return next(self.tim)

def colour(s,st='1',c='196',b='15'):
    # see https://stackabuse.com/how-to-print-colored-text-in-python/
    return f"\033[{st}m\033[38;5;{c}m\033[48;5;{b}m{s}\033[0;0m"


# Sample data

# The original problem was a maximum search with those weights;

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

(rows,cols) = weights.shape
weights = 9 - weights


(rows,cols) = 30,40
weights = np.ndarray((rows,cols))
for row  in range(rows):
    for col in range(cols):
        weights[row,col] = randrange(10)


# make the border of -1's around the board 
r1 = -1*np.ones(cols)
weights = np.insert(weights,rows,r1,axis=0)
weights = np.insert(weights,0,r1,axis=0)
weights = np.insert(weights,0,-1,axis=1)
weights = np.insert(weights,cols+1,-1,axis=1)

# print(weights)
costtab = np.ndarray((rows+2,cols+2,Length+2))
rowRange = range(1,rows+1)
colRange = range(1,cols+1)

def trace():
    path=set()
    for row in rowRange:     # range(1,rows+1)
        for col in colRange:     # range(1,cols+1)
            if weights[row,col]<0:
                path=path.union({(row,col)})
    return path
            

def cost(row,col,Sum,length):
    global lowcost, solution
    w = weights[row,col]
    if w >= 0:
        if Sum+costtab[row,col,length] < lowcost:
            s = Sum+w
            if length>1:
                weights[row,col] -= 12 # mark as occupied
                cost(row-1,col,s,length-1)
                cost(row+1,col,s,length-1)
                cost(row,col-1,s,length-1)
                cost(row,col+1,s,length-1)
                weights[row,col] += 12 # restore original value
            elif s<lowcost:
                lowcost = s
                if flag:
                    solution = trace().union({(row,col)})

print(f'Board {rows} × {cols}, path length {Length}.')
                    
# start timing

t=timer()

# initialise costtab

for row in range(1,rows+1):
    for col in range(1,cols+1):
        for cut in range(1, Length+1):
            costtab[row,col,cut] = weights[row,col]
flag = False # indicates preliminary scan

for cut in range(2, Length+1):
    lowcost = infinity
    for row in range(1,rows+1,1):
        for col in range(1,cols+1):
            cost(row,col,0,cut)
            costtab[row,col,cut] = lowcost

lowcost = infinity # restore lowcost
flag = True # serious scan
for row in range(1,rows+1):
    for col in range(1,cols+1):
        cost(row,col,0,Length)


for row in range(1,rows+1):
    for col in range(1,cols+1):
        w = weights[row,col]
        if (row,col) in solution:
            ch = colour(int(w),b='81')
        else:
            ch = colour(int(w),st='2',c='248')
        print(ch,end='' )
    print('')

print(f'Optimal path cost is {lowcost}. Timing {t.odczyt():.2f} s.')
        
        




            
    
    



