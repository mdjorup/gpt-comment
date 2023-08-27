class Comment:
    def __init__(self, comment: str, prefix: str = ""):
        self.comment = comment.strip()
        self.prefix = prefix

    def __str__(self):
        if self.prefix:
            return f"{self.prefix}{self.comment}"
        else:
            return self.comment

    def to_dict(self) -> dict:
        return {
            "comment_type": "general",
            "comment": self.comment,
        }

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

    def to_dict(self) -> dict:
        return {
            "comment_type": "quoted",
            "quote": self.quote,
            "comment": self.comment,
        }

    def class_repr(self):
        return (
            f"QuotedComment("
            f"comment={self.comment}, "
            f"quote={self.quote}, "
            f"start_index={self.start_index}, "
            f"length={self.length})"
        )
