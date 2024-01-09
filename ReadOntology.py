import xml.etree.ElementTree as ET
from collections import defaultdict


class Rules:
    def __init__(self, name, riskfactor1, riskfactor2, alter, dis, prob, stat, prio):
        self.rulenames = name
        self.disease = dis
        self.rulefactor1 = riskfactor1
        self.rulefactor2 = riskfactor2
        self.rulealter = alter
        self.ruleProb = float(prob)
        self.ruleStatus = stat
        self.rulePrio = float(prio)

        def getRuleName(self):
            return self.rulenames

        def getRuleFactor1(self):
            return self.rulefactor1

        def getRuleFactor2(self):
            return self.rulefactor2

        def getRuleAlter(self):
            return self.rulealter

        def getRuleDisease(self):
            return self.disease

        def getProb(self):
            return self.ruleProb

        def getPrio(self):
            return self.rulePrio

        def getRuleStatus(self):
            return self.ruleStatus


class ReadOntology:
    def __init__(self):
        self.network_map = defaultdict(list)
        self.parts_found = set()
        self.node_counter = 0
        self.rule_list_obj = defaultdict(list)
        self.rule_part_list_obj = {}
        self.probs = 0.0
        self.rules = None

        self.values = None
        self.xml_file = "padc.xml"
        self.doc = ET.parse(self.xml_file).getroot()
        self.x_path = ET.XPathEvaluator(self.doc)
