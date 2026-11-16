"""Port du Parser, NFA et DFA du projet DAAR 1 pour la V2."""

class RegexError(ValueError):
    pass


class Parser:
    def __init__(self, pattern):
        if not pattern or not pattern.strip() or len(pattern) > 100:
            raise RegexError("Motif vide ou trop long.")
        self.pattern = pattern
        self.pos = 0

    def peek(self):
        return (
            self.pattern[self.pos]
            if self.pos < len(self.pattern)
            else ""
        )

    def parse(self):
        tree = self.alt()
        if self.peek():
            raise RegexError("Parenthese fermante inattendue.")
        return tree

    def alt(self):
        node = self.concat()
        while self.peek() == "|":
            self.pos += 1
            node = ("alt", node, self.concat())
        return node

    def concat(self):
        node = None
        while self.peek() and self.peek() not in "|)":
            right = self.rep()
            node = (
                right if node is None
                else ("concat", node, right)
            )
        return node if node is not None else ("eps",)

    def rep(self):
        node = self.atom()
        while self.peek() and self.peek() in "*+?":
            operator = self.peek()
            self.pos += 1
            name = {
                "*": "star",
                "+": "plus",
                "?": "opt",
            }[operator]
            node = (name, node)
        return node

    def atom(self):
        ch = self.peek()
        if not ch:
            raise RegexError("Expression incomplete.")

        self.pos += 1

        if ch == "(":
            node = self.alt()
            if self.peek() != ")":
                raise RegexError("Parenthese non fermee.")
            self.pos += 1
            return node

        if ch == ".":
            return ("dot",)

        if ch == "\\":
            if not self.peek():
                raise RegexError("Antislash sans caractere.")
            ch = self.peek()
            self.pos += 1
            return ("char", ch)

        if ch in "*+?)":
            raise RegexError("Operateur inattendu.")

        return ("char", ch)


class AutomateV2:
    def __init__(self, pattern):
        tree = Parser(pattern.casefold()).parse()
        self.edges = []
        self.start, self.accept = self.build(tree)
        self.initial = self.closure({self.start})
        self.transitions = {}

    def state(self):
        if len(self.edges) >= 512:
            raise RegexError("Automate trop grand.")
        self.edges.append([])
        return len(self.edges) - 1

    def edge(self, source, symbol, target):
        self.edges[source].append((symbol, target))

    def build(self, tree):
        kind = tree[0]

        if kind == "concat":
            a, b = self.build(tree[1])
            c, d = self.build(tree[2])
            self.edge(b, None, c)
            return a, d

        start, end = self.state(), self.state()

        if kind == "eps":
            self.edge(start, None, end)

        elif kind == "char":
            self.edge(start, tree[1], end)

        elif kind == "dot":
            self.edge(start, "ANY", end)

        elif kind == "alt":
            for branch in (tree[1], tree[2]):
                a, b = self.build(branch)
                self.edge(start, None, a)
                self.edge(b, None, end)

        elif kind in ("star", "plus", "opt"):
            a, b = self.build(tree[1])
            self.edge(start, None, a)
            self.edge(b, None, end)

            if kind in ("star", "plus"):
                self.edge(b, None, a)

            if kind in ("star", "opt"):
                self.edge(start, None, end)

        return start, end

    def closure(self, states):
        result = set(states)
        stack = list(states)

        while stack:
            for symbol, dest in self.edges[stack.pop()]:
                if symbol is None and dest not in result:
                    result.add(dest)
                    stack.append(dest)

        return frozenset(result)

    def step(self, states, char):
        key = (states, char)

        if key not in self.transitions:
            targets = {
                dest
                for state in states
                for symbol, dest in self.edges[state]
                if symbol is not None
                and (symbol == "ANY" or symbol == char)
            }

            self.transitions[key] = self.closure(targets)

            if len(self.transitions) > 100_000:
                raise RegexError("Trop de transitions DFA.")

        return self.transitions[key]

    def fullmatch(self, word):
        states = self.initial

        for char in word.casefold():
            states = self.step(states, char)

            if not states:
                return False

        return self.accept in states
