class VoteOrganizerRound:
    def __init__(self, elector, vote):
        self.elector    = elector
        self.vote  = vote

    def setElector(self, elector):
        self.elector = elector

    def setVote(self, vote):
        self.vote = vote

    def getElector(self):
        return self.elector

    def getVote(self):
        return self.vote

class VoteContestationRound:
    def __init__(self, elector, vote):
        self.elector    = elector
        self.vote  = vote

    def setElector(self, elector):
        self.elector = elector

    def setVote(self, vote):
        self.vote = vote

    def getElector(self):
        return self.elector

    def getVote(self):
        return self.vote