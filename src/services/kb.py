import os

class KnowledgeBase:
    """TODO: this is not currently being used but might need later"""
    def __init__(self, kb_file: str=None):
        self.kb_file = kb_file
        self.content = {}

        if kb_file:
            self.load_from_file(kb_file)
    
    def load_from_file(self, path: str):
        """Load knowledge base from file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.content = f.read()
        else:
            print("Warning: no knowledge base found")
            return ""
