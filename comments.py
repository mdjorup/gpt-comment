


class Comment:
    
    def __init__(self, comment: str, prefix : str = ""):
        self.comment = comment.strip()
        self.prefix = prefix

    def __str__(self):
        if self.prefix:
            return f"{self.prefix}{self.comment}"
        else:
            return self.comment
        
    def class_repr(self):
        return f"Comment(comment={self.comment}, prefix={self.prefix})"  
    


class QuotedComment(Comment):
    
    def __init__(self, comment, quote, start_index, length):
        super().__init__(comment)
        self.quote = quote
        self.start_index = start_index
        self.length = length

    def __str__(self):
        return f'"{self.quote}" - {self.comment}'   

    def class_repr(self):
        return f"QuotedComment(comment={self.comment}, quote={self.quote}, start_index={self.start_index}, length={self.length})"  
    