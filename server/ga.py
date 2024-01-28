import random

def create_graph_with_manhattan_distances(places):
    """
    Create a graph where nodes are attractions with provided latitudes and longitudes,
    and edges are the Manhattan distances between these attractions.

    Args:
        places (list of dicts): Each dict contains 'name', 'lat', and 'long' keys for an attraction.

    Returns:
        dict: Graph representing attractions and Manhattan distances between them.
    """
    graph = {}

    # Generate distances between each pair of attractions
    for i, place1 in enumerate(places):
        attraction1 = place1.name
        graph[attraction1] = {}
        for j, place2 in enumerate(places):
            attraction2 = place2.name
            if i != j:
                # Calculate Manhattan distance
                distance = abs(place1.lat - place2.lat) + abs(place1.lon - place2.lon)
                graph[attraction1][attraction2] = distance

    return graph

def run_genetic_algorithm(graph, initial_pop_size, start_attraction, end_attraction, final_path_size, generations, initial_mutation_rate, minimum_mutation_rate, all_start_end_points, debug = False):
    """Runs the genetic algorithm for itinerary planning.

    Args:
        graph (dict): The graph representing attractions and distances between them.
        initial_pop_size (int): The size of the initial population.
        start_attraction (str): The starting attraction.
        end_attraction (str): The ending attraction.
        final_path_size (int): The length of each path in the population.
        generations (int): The number of generations to run the algorithm.
        initial_mutation_rate (float): The initial mutation rate.
        minimum_mutation_rate (float): The minimum mutation rate.

    Returns:
        bestPath (list): The best path found by the genetic algorithm.
        bestFitness (float): The fitness of the best path.
    """
    bestPath = []
    bestFitness = float('inf')
    decay_rate = (initial_mutation_rate - minimum_mutation_rate) / generations
    population = CreateInitialPopulation(initial_pop_size, graph, start_attraction, end_attraction, final_path_size, all_start_end_points)
        
    for generation in range(generations):
        RankList = [(i, calculate_path_distance(graph, path)) for i, path in enumerate(population)]
        RankList.sort(key=lambda item: item[1])
        
        mutation_rate = initial_mutation_rate - (generation * decay_rate)
        mutation_rate = max(mutation_rate, minimum_mutation_rate)
        
        currentBestFitness = RankList[0][1]  # The first element in the RankList is the best fitness
        
        if currentBestFitness < bestFitness:
            if debug:
                print(f"At generation {generation}, the fitness improved from {bestFitness} to {currentBestFitness}")
            bestFitness = currentBestFitness
            bestPath = population[RankList[0][0]]
            
        matingPool = CreateMatingPool(population, RankList)
        
        newPopulation = []
        
        size = len(population)
        for i in range(size//2):
            # Select two parents from the mating pool
            Parent1 = matingPool[random.randint(0, len(matingPool)-1)]
            Parent2 = matingPool[random.randint(0, len(matingPool)-1)]
            
            # Select the crossover section ignoring the first and last attractions        
            start_index = random.randint(1, len(Parent1)-2)
            end_index = random.randint(start_index, len(Parent1)-2)
            
            child = Crossover(Parent1, Parent2, start_index, end_index, all_start_end_points)
            
            
            # Randomly mutate the child
            if random.random() < mutation_rate:
                child = Mutate(child, graph, all_start_end_points)
                
            newPopulation.append(child)
            
        # Retain size/2 best individuals from the previous population
        newPopulation += population[:size//2]
        population = newPopulation
    return bestPath, bestFitness

def calculate_path_distance(graph, path):
    """Calculates the total distance of a path based on the graph distances.

    Args:
        graph (dict): A dictionary representing the graph of attractions.
        path (list): A list of attractions representing the path.

    Returns:
        total_distance (float): The total distance of the given path.
    """
    total_distance = 0
    for i in range(len(path) - 1):
        # Get the distance between the current attraction and the next, and add it to the total distance
        total_distance += graph[path[i]].get(path[i + 1], float('inf'))
    return total_distance

def Mutate(Child, graph, all_start_end_points):
    """Mutates the child by performing one of two operations:
    1. Reversing the order of a random subset of the child, excluding the first and last elements.
    2. Replacing an attraction with an attraction not in the path, excluding the replacement of the first and last elements.

    Args:
        Child (list): The child to be mutated.
        graph (dict): A dictionary representing the graph of attractions.
        all_start_end_points (list): List of all start and end attractions for each day

    Returns:
        Child (list): The mutated child.
    """
    mutation_type = random.choice(['reverse', 'replace'])
    
    if mutation_type == 'reverse':
        # Reverse mutation
        if len(Child) > 3:  # Ensure there are elements to reverse (excluding the first and last)
            start_index = random.randint(1, len(Child) - 3)
            end_index = random.randint(start_index, len(Child) - 2)
            Child[start_index:end_index+1] = Child[start_index:end_index+1][::-1]
        
    elif mutation_type == 'replace':
        # Replacement mutation
        # Ensure there's an element to replace (excluding the first and last)
        if len(Child) > 2:
            # Get all possible attractions that are not in the child and not in all_start_end_points
            possible_replacements = set(graph.keys()) - set(Child) - set(all_start_end_points)
            if possible_replacements:
                # Select a random attraction from the child to replace (excluding the start and end attractions)
                index_to_replace = random.randint(1, len(Child) - 2)
                # Select a random replacement attraction
                replacement_attraction = random.choice(list(possible_replacements))
                # Replace the attraction in the child
                Child[index_to_replace] = replacement_attraction
    return Child

def Crossover(Parent1, Parent2, Start_Index, End_Index, all_start_end_points):
    """Performs crossover between two parents and returns the child

    Args:
        Parent1 (list): The first parent (path of attractions)
        Parent2 (list): The second parent (path of attractions)
        Start_Index (int): The start index of the crossover section
        End_Index (int): The end index of the crossover section
        all_start_end_points (list): List of all start and end attractions for each day

    Returns:
        child (list): The child generated after crossover
    """
    child = []
    
    # Ensure that the crossover does not include the start and end positions
    Start_Index = max(Start_Index, 1)
    End_Index = min(End_Index, len(Parent1) - 2)
    
    # Slice from Parent1 for the crossover section
    p1_section = Parent1[Start_Index:End_Index+1]
    
    # Remainder of the attractions that will be filled in from Parent2
    remainder = [attraction for attraction in Parent2 if attraction not in p1_section]
    
    # Construct the child: attractions before the crossover section from Parent2, 
    # the crossover section from Parent1, and the rest from Parent2
    child = remainder[:Start_Index] + p1_section + remainder[Start_Index:]
    
    # Ensure that all attractions are included exactly once
    # Find missing attractions and duplicate attractions in the child
    all_attractions = set(Parent1) - set(all_start_end_points)
    child_attractions = set(child)
    missing_attractions = list(all_attractions - child_attractions)
    
    # Check for any missing attractions in the child and replace the duplicates with the missing attractions
    if missing_attractions:
        for i in range(1, len(child) - 1):  # Ensure we don't replace the start and end points
            if child[i] in all_start_end_points or child.count(child[i]) > 1:
                child[i] = missing_attractions.pop()
                
                if not missing_attractions:
                    break

    return child



def calculate_distance_attraction(graph, attraction1, attraction2):
    """Calculates the distance between two attractions based on a graph

    Args:
        graph (dict): A dictionary representing the graph of attractions.
        attraction1 (str): The name of the first attraction.
        attraction2 (str): The name of the second attraction.

    Returns:
        distance (float): The distance between the two attractions. Returns float('inf') if there is no direct path.
    """
    # Return the distance from the graph if it exists, otherwise return infinity
    return graph.get(attraction1, {}).get(attraction2, float('inf'))

def CreateMatingPool(population, RankList, tournament_size=3):
    """
    Implements tournament selection for a genetic algorithm's parent selection.
    In each tournament, a subset of individuals is chosen at random, and the one with the best fitness
    (highest rank) is selected for the mating pool.

    Args:
        population (list): A list of paths (each path is a list of attractions) from which the mating pool is to be created.
        RankList (list): A list of tuples (index, fitness score) sorted in ascending order of fitness (lower is better).
        tournament_size (int): The number of individuals to be selected for each tournament. Default is 3.

    Returns:
        mating_pool (list): A list of paths selected from the population to form the mating pool.
    """
    
    matingPool = []
    
    for _ in range(len(population)):
        # Conduct a tournament
        tournament = random.sample(RankList, tournament_size)
        # Select the winner with the best fitness (lowest score)
        winner = min(tournament, key=lambda item: item[1])
        # Append the path corresponding to the winner to the mating pool
        matingPool.append(population[winner[0]])
                     
    return matingPool


def CreateInitialPopulation(size, graph, start_attraction, end_attraction, final_path_size, all_start_end_points):
    """Generates the initial population for the genetic algorithm
    
    Args:
        size (int): The size of the list (initial_population) to be returned.
        graph (dict): A dictionary representing the graph of attractions.
        start_attraction (str): The starting attraction.
        end_attraction (str): The ending attraction.
        final_path_size (int): The length of each path in the population.
        all_start_end_points (list): List of all start and end attractions for each day.

    Returns:
        initial_population (list): A list of paths (a permutation of attractions) of size = size.
    """
    initial_population = []
    attractions = list(graph.keys())

    # Remove all start and end attractions from the list of attractions to visit
    attractions = [attraction for attraction in attractions if attraction not in all_start_end_points]

    for i in range(size):
        path = [start_attraction]  # Initialize path with start_attraction
        remaining_attractions = set(attractions) - {start_attraction, end_attraction}
        
        # Random initialization
        path += random.sample(list(remaining_attractions), min(len(remaining_attractions), final_path_size - 2))

        path.append(end_attraction)  # Append the end attraction to the path
        if path not in initial_population:
            initial_population.append(path)
    
    return initial_population


