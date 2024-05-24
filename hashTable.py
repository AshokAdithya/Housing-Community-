import json

class Node:
    def __init__(self,key,value):
        self.key=key
        self.value=value
        self.next=None

class HashTable:
    def __init__(self, cap):
        self.cap = cap
        self.size = 0
        self.table = [None] * cap

    def _hash(self, key):
        return hash(key) % self.cap

    def insert(self, key, value):
        index = self._hash(key)
        if self.table[index] is None:
            self.table[index] = Node(key, value)
            self.size += 1
        else:
            current = self.table[index]
            while current:
                if current.key == key:
                    current.value = value
                    return
                current = current.next
            new_node = Node(key, value)
            new_node.next = self.table[index]
            self.table[index] = new_node
            self.size += 1

    def search(self, key):
        index = self._hash(key)
        current = self.table[index]
        while current:
            if current.key == key:
                return current.value
            current = current.next
        return None

    def to_dict(self):
        result = {}
        for i in range(self.cap):
            current = self.table[i]
            while current:
                result[current.key] = current.value
                current = current.next
        return result

    def save_to_file(self, file_name):
        with open(file_name, 'w') as file:
            json.dump(self.to_dict(), file)

    def load_from_file(self, file_name, cap):
        try:
            with open(file_name, 'r') as file:
                data_dict = json.load(file)
            self.cap = cap
            self.size = 0
            self.table = [None] * cap
            for key, value in data_dict.items():
                self.insert(key, value)
            return self

        except FileNotFoundError:
            self.cap = cap
            self.size = 0
            self.table = [None] * cap
            return self