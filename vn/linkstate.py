class LinkStateDB:
    def __init__(self):
        self.me = None
        self.neighbours = {}
        self.my_seq = 0
        self.lsdb = {}
    def set_neighbourhood(self, tuples):
        me = None
        nbrs = {}
        for letter, ip, port, cost in tuples:
            if cost == 0:
                me = letter
            else :
                nbrs[letter] = (ip, port, cost)
        if me is None:
            raise ValueError("LINK-STATE has no zero-cost tuple")
        self.me = me
        self.neighbours = nbrs
    def build_own_lsp(self):
        self.my_seq += 1
        links = {letter: cost for letter, (ip, port, cost) in self.neighbours.items()}
        self.lsdb[self.me] = (self.my_seq, links)
        return self.me, self.my_seq, links
    def accept_lsp(self, origin, seq, links):
        if origin == self.me:
            return False
        known = self.lsdb.get(origin)
        if known is not None and seq <= known[0]:
            return False
        self.lsdb[origin] = (seq, links)
        return True
    def forward_targets(self, sender_addr):
        return [(ip, port)
                for (ip, port, cost) in self.neighbours.values()
                if (ip, port) != sender_addr]
    def graph_text(self):
        nodes = set(self.lsdb)
        for seq, links in self.lsdb.values():
            nodes.update(links)
        nodes = sorted(nodes)

        def cost(a,b):
            if a in self.lsdb:
                links = self.lsdb[a][1]
                if b in links:
                    return links[b]

            if b in self.lsdb:
                links = self.lsdb[b][1]
                if a in links:
                    return links[a]

            return -1


        lines = ["# known graph, node order: " + " ".join(nodes)]
        for i, a in enumerate(nodes[:-1]):
            row = [str(cost(a,b)) for b in nodes[i+1:]]
            lines.append("\t"*i + "\t".join(row))
        return "\n".join(lines)

