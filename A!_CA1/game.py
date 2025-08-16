from collections import deque
import copy
import heapq


class Game:
    def __init__(self, game_map_string):
        self.game_map = []
        lines = game_map_string.split('\n')
        for i in range(len(lines)):
            line = [cell.split("/") for cell in lines[i].strip().split()]
            self.game_map.append(line)
            
        self.height = len(self.game_map)
        self.width = len(self.game_map[0])
        number_of_boxes = game_map_string.count('B')
        number_of_portals = game_map_string.count('P')
        self.boxes = [0] * number_of_boxes
        self.goals = [0] * number_of_boxes
        self.portals = [[] for _ in range(number_of_portals // 2)]
        self.map_size = len(lines)
        self.num_boxes = number_of_boxes
        self.most_left_accessible_column = self.width
        self.most_right_accessible_column = 0
        self.most_top_accessible_row = self.height
        self.most_bottom_accessible_row = 0
        
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                static_element = '.'
                for k in range(len(self.game_map[i][j])):
                    if self.game_map[i][j][k][0] == 'H':
                        self.player_pos = (i, j)
                    elif self.game_map[i][j][k][0] == 'B':
                        idx = int(self.game_map[i][j][k][1:]) - 1
                        self.boxes[idx] = (i, j)
                    elif self.game_map[i][j][k][0] == 'G':
                        idx = int(self.game_map[i][j][k][1:]) - 1
                        self.goals[idx] = (i, j)
                        static_element = self.game_map[i][j][k]
                    elif self.game_map[i][j][k][0] == 'P':
                        idx = int(self.game_map[i][j][k][1:]) - 1
                        self.portals[idx].append((i, j))
                        static_element = self.game_map[i][j][k]
                    elif self.game_map[i][j][k][0] == 'W':
                        static_element = 'W'
                        
                # we only save the static element in the map array for optimization
                self.game_map[i][j] = static_element  
    ##################################################################################################################################
    def set_player_position(self, pos):
        self.player_pos = pos
    
    def set_box_positions(self, boxes):
        self.boxes = [box for box in boxes]
        
    def get_map_size(self):
        return [self.height, self.width]

    def get_box_locations(self):
        return [box for box in self.boxes]
    
    def get_goal_locations(self):
        return [goal for goal in self.goals]
    
    def get_portal_locations(self):
        return self.portals
    
    def get_player_position(self):
        return self.player_pos
    
    def is_wall(self, pos):
        return self.__is_pos_out_of_bounds(pos)
    
    # It's time consuming
    def get_elements_in_position(self, pos):
        if self.__is_pos_out_of_bounds(pos):
            return ["W"]
        elements = []
        if self.game_map[pos[0]][pos[1]] != '.':
            elements.append(self.game_map[pos[0]][pos[1]])
        for i in range(len(self.boxes)):
            if self.boxes[i] == pos:
                elements.append(f'B{i + 1}')
        if self.player_pos == pos:
            elements.append('H')
        if len(elements) == 0:
            elements.append('.')
        return elements

    # It's time consuming
    def get_map(self):
        game_map_copy = [[[cell] for cell in row] for row in self.game_map]
        for i in range(len(self.boxes)):
            box = self.boxes[i]
            game_map_copy[box[0]][box[1]].append(f'B{i + 1}')
        game_map_copy[self.player_pos[0]][self.player_pos[1]].append('H')
        
        result = []
        for i in range(len(game_map_copy)):
            row = []
            for j in range(len(game_map_copy[i])):
                cell = game_map_copy[i][j]
                if len(cell) > 1 and cell[0] == '.':
                    cell = cell[1:]
                row.append('/'.join(cell))
            result.append('\t'.join(row))
        return '\n'.join(result) 
    
    def display_map(self):
        print(self.get_map())   
                      
    def apply_move(self, direction):
        direction_map = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
        direction = direction_map[direction]
        human_new_pos = self.__calculate_new_pos(self.player_pos, direction)
        
        if self.__is_pos_out_of_bounds(human_new_pos):
            return False
        
        box_id = self.__get_element_id_in_cell(human_new_pos, 'B')
        if box_id is not None:
            box_new_pos = self.__calculate_new_pos(self.boxes[box_id - 1], direction)
            if not self.__validate_box_new_pos(box_new_pos):
                return False
            self.boxes[box_id - 1] = box_new_pos
        self.player_pos = human_new_pos
        return True
        
    def apply_moves(self, moves):
        for move in moves:
            try:
                self.apply_move(move)
            except ValueError:
                pass
        
    def is_game_won(self):
        for i in range(len(self.boxes)):
            if self.boxes[i] != self.goals[i]:
                return False
        return True
    
    def is_solution_valid(self, solution):
        self.apply_moves(solution)
        return self.is_game_won()
        
    def __calculate_new_pos(self, current_pos, direction):
        dy, dx = direction
        new_pos = (current_pos[0] + dy, current_pos[1] + dx)
        portal_id = self.__get_element_id_in_cell(new_pos, 'P')
        if portal_id is not None:
            portal_idx = portal_id - 1
            if new_pos == self.portals[portal_idx][0]:
                return (self.portals[portal_idx][1][0] + dy, self.portals[portal_idx][1][1] + dx)
            return (self.portals[portal_idx][0][0] + dy, self.portals[portal_idx][0][1] + dx)
        return new_pos
            
    def __is_pos_out_of_bounds(self, pos):
        return (pos[0] < 0 or pos[0] >= self.height or 
                pos[1] < 0 or pos[1] >= self.width or 
                self.game_map[pos[0]][pos[1]][0] == 'W')
    
    def __validate_box_new_pos(self, pos):
        if self.__is_pos_out_of_bounds(pos) or self.__get_element_id_in_cell(pos, 'B') is not None:
            return False
        return True
    
    def __get_element_id_in_cell(self, pos, element):
        if pos[0] < 0 or pos[0] >= self.height or pos[1] < 0 or pos[1] >= self.width:
            return None
        if element == "B":
            for i in range(len(self.boxes)):
                if self.boxes[i] == pos:
                    return i + 1
        if element == self.game_map[pos[0]][pos[1]][0]:
            return int(self.game_map[pos[0]][pos[1]][1:])
        return None                



dir_map = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}

def bfs(game_map):
    game = Game(game_map)
    queue = deque([(game.get_player_position(), tuple(game.get_box_locations()), "")])
    mark = set()
    while queue:
        mike, boxes, path = queue.popleft()
        if boxes == tuple(game.get_goal_locations()):
            return path
        s = (mike, boxes)
        if s in mark:
            continue
        mark.add(s)
        for d in dir_map:
            game.set_player_position(mike)
            game.set_box_positions(list(boxes))
            if game.apply_move(d):
                neeew = (game.get_player_position(), tuple(game.get_box_locations()), path + d)
                queue.append(neeew)
    return "No solution"
#######################################################################################################
def dfs(game_map):
    game = Game(game_map)
    stack = [(game.get_player_position(), tuple(game.get_box_locations()), "")]
    mark = set()
    while stack:
        mike, boxes, path = stack.pop()
        if boxes == tuple(game.get_goal_locations()):
            return path
        s = (mike, boxes)
        if s in mark:
            continue
        mark.add(s)
        for d in dir_map:
            game.set_player_position(mike)
            game.set_box_positions(list(boxes))
            if game.apply_move(d):
                neew = (game.get_player_position(), tuple(game.get_box_locations()), path + d)
                stack.append(neew)
    return "No solution"
#########################################################################################
def ids(game_map):
    depth = 0
    while 1:
        mark = set()
        path = f_rec(Game(game_map), depth, mark, "")
        if path is not None:
            return path
        depth += 1

def f_rec(game, depth, mark, path):
    mike = game.get_player_position()
    boxes = tuple(game.get_box_locations())
    if boxes == tuple(game.get_goal_locations()):
        return path
    if depth == 0:
        return None
    s = (mike, boxes)
    if s in mark:
        return None
    mark.add(s)
    for d in dir_map:
        game.set_player_position(mike)
        game.set_box_positions(list(boxes))
        if game.apply_move(d):
            neew = f_rec(game, depth - 1, mark, path + d)
            if neew is not None:
                return neew
    mark.remove(s)
    return None
#######################################################################################
def MNH(first_point, second_point):
    x1 = first_point[0]
    x2 = first_point[1]
    y1 = second_point[0]
    y2 = second_point[1]
    manhatan = abs(x1 - y1) + abs(x2 - y2)
    return manhatan

def heuristic_1(game_map):
    game = Game(game_map)
    goals = game.get_goal_locations()
    def temp_function(now):
        ans = 0
        for i in range(len(now[1])):
            ans += MNH(now[0], now[1][i]) + MNH(now[1][i], goals[i])
        return ans
    return temp_function

def a_star_1(game_map):
    game = Game(game_map)
    temp_function = heuristic_1(game_map)
    H0 = (game.get_player_position(), tuple(game.get_box_locations()))
    h = temp_function(H0)
    goals = game.get_goal_locations()
    g = 0
    f = g + h
    nodes = [(f, g, H0, "")]
    mark = {H0: g}
    while nodes:
        node = heapq.heappop(nodes)
        f = node[0]
        g = node[1]
        s = node[2]
        path = node[3]
        mike, boxes = s
        if list(boxes) == goals:
            return path
        neighbors = []
        for d in dir_map:
            game_copy = Game(game_map)
            game_copy.set_player_position(mike)
            game_copy.set_box_positions(list(boxes))
            if game_copy.apply_move(d):
                neew = (game_copy.get_player_position(), tuple(game_copy.get_box_locations()))
                neighbors.append((d, neew))
        for d, neew in neighbors:
            now = g + 1
            if neew not in mark or now < mark[neew]:
                mark[neew] = now
                ff = now + temp_function(neew)
                heapq.heappush(nodes, (ff, now, neew, path + d))
                
    return None
#############################################################################################3
def PO(p1, p2, portals):
    H0 = MNH(p1, p2)
    for portal in portals:
        H1 = min(MNH(p1, portal[0]) + MNH(portal[1], p2),MNH(p1, portal[1]) + MNH(portal[0], p2))
        H0 = min(H0, H1)
    return H0

def heuristic_2(game):
    goals = game.get_goal_locations()
    portals = game.get_portal_locations()
    def temp_function(s):
        mike, boxes = s
        if not boxes:
            return 0
        dis = []
        for box in boxes:
            distance = PO(mike, box, portals)
            dis.append(distance)
        mn1 = min(dis)
        mn2 = 0
        for i in range(len(boxes)):
            mn2 += PO(boxes[i], goals[i], portals)
        ans = mn1 + mn2
        return ans
    return temp_function


def a_star_2(game_map):
    game = Game(game_map)
    temp_function = heuristic_2(game)
    H0 = (game.get_player_position(), tuple(game.get_box_locations()))
    h = temp_function(H0)
    goals = game.get_goal_locations()
    g = 0
    f = g + h
    nodes = [(f, g, H0, "")]
    mark = {H0: g}
    while nodes:
        node = heapq.heappop(nodes)
        f = node[0]
        g = node[1]
        s = node[2]
        path = node[3]
        mike, boxes = s
        if list(boxes) == goals:
            return path
        neighbors = []
        for d in dir_map:
            game_copy = Game(game_map)
            game_copy.set_player_position(mike)
            game_copy.set_box_positions(list(boxes))
            if game_copy.apply_move(d):
                neew = (game_copy.get_player_position(), tuple(game_copy.get_box_locations()))
                neighbors.append((d, neew))
        for d, neew in neighbors:
            now = g + 1
            if neew not in mark or now < mark[neew]:
                mark[neew] = now
                ff = now + temp_function(neew)
                heapq.heappush(nodes, (ff, now, neew, path + d))
                
    return None
##################################################################################################
def weighted_a_star(game_map, w=5):
    game = Game(game_map)
    temp_function = heuristic_2(game)
    H0 = (game.get_player_position(), tuple(game.get_box_locations()))
    h = temp_function(H0)
    goals = game.get_goal_locations()
    g = 0
    f = g + w * h
    nodes = [(f, g, H0, "")]
    mark = {H0: g}
    while nodes:
        node = heapq.heappop(nodes)
        f = node[0]
        g = node[1]
        s = node[2]
        path = node[3]
        mike, boxes = s
        if list(boxes) == goals:
            return path
        neighbors = []
        for d in dir_map:
            game_copy = Game(game_map)
            game_copy.set_player_position(mike)
            game_copy.set_box_positions(list(boxes))
            if game_copy.apply_move(d):
                neew = (game_copy.get_player_position(), tuple(game_copy.get_box_locations()))
                neighbors.append((d, neew))
        for d, neew in neighbors:
            now = g + 1
            if neew not in mark or now < mark[neew]:
                mark[neew] = now
                ff = now + w * temp_function(neew)
                heapq.heappush(nodes, (ff, now, neew, path + d))
                
    return None