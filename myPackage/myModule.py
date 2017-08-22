import datetime
import pandas as pd
import numpy as np
from numpy.random import randint
from pandas_datareader import data, wb

day = 1
month = 1

start = datetime.datetime(2017, 1, 1)
end = datetime.datetime(2017, 8, 1)

stock = None
nodes = 0
population = 10
generations = 1000

chromosones = [[]]
constraints = []
domain = ['Buy','Hold','Sell']

def get_dataframe():

    global stock, nodes
    stock = data.DataReader("FUNCOM.OL", "yahoo", start, end)
    #quote = data.get_quote_yahoo('FUNCOM.OL')
    
    nodes = len(stock.index)
    
    # Get just the close
    close = stock['Adj Close']
    # Get the difference in price from previous step
    delta = close.diff()
    # Assign new column and set its value
    stock['Change'] = delta
    # Get rid of the first row, which is NaN since it did not have a previous 
    # row to calculate the differences
    delta = delta[1:] 
    
    # Make the positive gains (up) and negative gains (down) Series
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    
    # Calculate the EWMA
    #roll_up = pd.ewma(up, 14)            # Will be deprecated in future versions
    #roll_down = pd.ewma(down.abs(), 14)  # Will be deprecated in future versions
    roll_up = up.ewm(com=14, min_periods=14, adjust=True).mean()
    roll_down = down.abs().ewm(com=14, min_periods=14, adjust=True).mean()
    
    # Calculate the RSI based on EWMA
    RS = roll_up / roll_down
    RSI = 100.0 - (100.0 / (1.0 + RS))
    
    # Assign new column and set its value
    stock['RSI'] = RSI
            
def initiate_population():

    # Special case for first element in array.
    chromosones[0].append(domain[randint(0,3)])

    # Create x instances of new rows (population).
    for i in range(population - 1):
        chromosones.append([domain[randint(0,3)]])

        # Generate as many genes as there are nodes, and gives them a domain value.
        for j in range(nodes - 1):
            chromosones[i].append(domain[randint(0,3)])

    # Special case for last row. Doesn'n get filled as normal.
    for k in range(nodes - 1):
        chromosones[-1].append(domain[randint(0,3)])

def chromosome_pair_up():

    parent_pair_up = []
        
    for gen in range(generations):
    
        # Creates a list with x unique numbers.
        # Will work as a random pair up for parents chromosomes.
        for x in range(population):
            y = randint(0,population)
            while y in parent_pair_up:
                y = randint(0,population)
            parent_pair_up.append(y)
        
        # Decide which two genes for 2-point crossover.
        x = randint(0,nodes)
        y = randint(0,nodes)
        while y == x:
            y = randint(0,nodes)
        
        for index in range(population):
    
            # Handle both parents in each iteration. Skip every other.
            if index % 2 == 1:
                continue
    
            # Copy parent rows and add them to chromosomes array to be further modified as children.
            chromosones.append(chromosones[parent_pair_up[index]][:])
            chromosones.append(chromosones[parent_pair_up[index+1]][:])
            
            #print(str(parent_pair_up[index]) + ' is matched with ' + str(parent_pair_up[index+1]))
    
            # 2-point crossover on newly created children.
            chromosones[population+index][x] = chromosones[parent_pair_up[index+1]][x]
            chromosones[population+index][y] = chromosones[parent_pair_up[index+1]][y]
            chromosones[population+index+1][x] = chromosones[parent_pair_up[index]][x]
            chromosones[population+index+1][y] = chromosones[parent_pair_up[index]][y]
            
            #print(str(x) + ' and ' + str(y) + ' selected for 2-point crossover')
    
            # Calculate probability for mutation. Is set to 2% pr child.
            probability = randint(1,100)
            if probability <= 2:
                chromosones[population+index][randint(0,nodes)] = domain[randint(0,3)]
            probability = randint(1,100)
            if probability <= 2:
                chromosones[population+index+1][randint(0,nodes)] = domain[randint(0,3)]
                   
        #print(chromosones)
        
        calculate_fitness()
        remove_population()
        print_fitness(gen)
        
        constraints[:] = []
        parent_pair_up[:] = []
    
def calculate_fitness():
        
    saldo = 1
    stocks = 0

    # Calculate fitness based on chromosones.
    # For each row
    for p in range(population * 2):            
        # For each node
        for q in range(nodes):                
            # Initiate BUY
            if stocks == 0 and chromosones[p][q] == 'Buy':                
                stocks = saldo / stock.iloc[q].Close
                saldo = 0                    
            # Initiate SELL
            elif stocks > 0 and chromosones[p][q] == 'Sell':                    
                saldo = stocks * stock.iloc[q].Close
                stocks = 0                    
        if stocks > 0:
            #print(str(p) + ': ' + 'Fitness is ' + '{:.2f}'.format(stocks * stock.iloc[-1].Close))
            # Calculate value based on last days closing price.
            constraints.append(stocks * stock.iloc[-1].Close)
        else:
            #print(str(p) + ': ' + 'Fitness is ' + '{:.2f}'.format(saldo))
            constraints.append(saldo)
        
        saldo = 1
        stocks = 0
    
def remove_population():
    
    # Remove half of population with least gain.
    for x in range(population):
        y = constraints.index(min(constraints))
        chromosones.remove(chromosones[y])
        constraints.remove(constraints[y])

def print_fitness(gen):
    
    # Prints every chromosone.
    #print('Gen: ' + str(gen))
    #for x in range(population):
    #    print(str(x) + ': ' + 'Fitness is ' + '{:.2f}'.format(constraints[x]))
    #print()
    
    # Prints only best chromosone.
    print('Gen ' + str(gen) + ': Best fitness: ' + '{:.2f}'.format(max(constraints)))
    
def remove_chromosome_redundancy():

    # Enforce 'Buy' / 'Sell' every second time and remove redundancy for better view. 
    # Example multiple occurrences 'Buy', 'Buy', 'Buy', 'Sell' => 'Buy', 'Hold', 'Hold', 'Sell'.
    for index in range(population):            

        for k in range(nodes):                    
            if chromosones[index][k] == 'Buy':                        
                for l in range(1, nodes - k - 1):                            
                    if chromosones[index][k + l] != 'Sell':
                        chromosones[index][k + l] = 'Hold'
                    else:
                        break
            elif chromosones[index][k] == 'Sell':                        
                for l in range(1, nodes - k - 1):                            
                    if chromosones[index][k + l] != 'Buy':
                        chromosones[index][k + l] = 'Hold'
                    else:
                        break

get_dataframe()
initiate_population()
chromosome_pair_up()

print(str(nodes) + ' nodes')
remove_chromosome_redundancy()
#print(chromosones)

stock['Indicator'] = chromosones[0]

# Prints from start to end
#print(pd.DataFrame(stock, index=[start, end]))

# Prints multiple columns
#print(pd.DataFrame(stock, columns=['Change', 'RSI', 'Indicator']))

# stock.index, stock.columns, stock['Text']
print(pd.DataFrame(stock['Indicator']))

# Prints whole DataFrame
#print(pd.DataFrame(stock))

# Sliced index print. Alternative iloc is index count
#print(stock.loc['20170103'])