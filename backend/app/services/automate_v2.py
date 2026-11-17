"""Moteur RegEx du projet DAAR 1 : analyse syntaxique, automate de
Thompson (NFA avec ε-transitions) et determinisation a la volee
(construction des sous-ensembles memorisee transition par transition)."""

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
        self.tree = tree
        self.edges = []
        self.start, self.accept = self.build(tree)
        self.initial = self.closure({self.start})
        self.transitions = {}

        # DFA construit a la volee : chaque ensemble d'etats du NFA recoit
        # un numero ; dfa[numero] = {caractere: numero suivant, -1 = puits}.
        self._numbers = {self.initial: 0}
        self._sets = [self.initial]
        self.dfa = [{}]
        self.accepting = [self.accept in self.initial]

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
        return self.fullmatch_normalized(word.casefold())

    def _expand(self, number, char):
        """Calcule (une seule fois) la transition DFA manquante."""
        target = self.step(self._sets[number], char)

        if not target:
            result = -1
        else:
            result = self._numbers.get(target)
            if result is None:
                result = len(self._sets)
                self._numbers[target] = result
                self._sets.append(target)
                self.dfa.append({})
                self.accepting.append(self.accept in target)

        self.dfa[number][char] = result
        return result

    def fullmatch_normalized(self, word):
        """Comme fullmatch, pour un mot deja en minuscules (termes de l'index).

        Cout : une lecture de dictionnaire par caractere une fois les
        transitions connues, soit O(|mot|).
        """
        dfa = self.dfa
        state = 0

        for char in word:
            following = dfa[state].get(char)
            if following is None:
                following = self._expand(state, char)
            if following < 0:
                return False
            state = following

        return self.accepting[state]

MAX_PREFIXES = 16


def literal_prefixes(tree):
    """Prefixes litteraux possibles des mots reconnus par l'expression.

    Renvoie (prefixes, exact) : tout mot reconnu commence par l'un des
    `prefixes` ; `exact` vaut True si l'expression ne reconnait que ces
    chaines. Un prefixe vide signifie « aucune contrainte ».

    Exemples : alic.* -> ["alic"] ; (love|heart) -> ["love", "heart"] ;
    k.ng -> ["k"] ; .*ing -> [""].
    """
    kind = tree[0]

    if kind == "char":
        return [tree[1]], True
    if kind == "eps":
        return [""], True
    if kind == "plus":
        return literal_prefixes(tree[1])[0], False
    if kind == "alt":
        left, left_exact = literal_prefixes(tree[1])
        right, right_exact = literal_prefixes(tree[2])
        return left + right, left_exact and right_exact
    if kind == "concat":
        left, left_exact = literal_prefixes(tree[1])
        if not left_exact:
            return left, False
        right, right_exact = literal_prefixes(tree[2])
        if len(left) * len(right) > MAX_PREFIXES:
            return left, False
        return [a + b for a in left for b in right], right_exact

    # dot, star, opt : le mot peut commencer par n'importe quoi.
    return [""], False
