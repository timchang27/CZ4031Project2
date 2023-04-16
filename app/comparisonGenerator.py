import json
import re
import itertools
import copy

class comparisonGeneartor(object):
    def __init__(self, QEPTree1, QEPTree2):
        self.QEPTree1 = QEPTree1
        self.QEPTree2 = QEPTree2
        self.joinCondition1 = {}
        self.joinCondition2 = {}
        self.relationSpecificOperations1 = self._getRelationSpecificOperations(self.QEPTree1)
        self.joinDictionary1 = self._getJoinConditions(self.QEPTree1)
        self.relationSpecificOperations2 = self._getRelationSpecificOperations(self.QEPTree2)
        self.joinDictionary2 = self._getJoinConditions(self.QEPTree2)
        
    def formatRelationSpecificOperations(self):
        formatted1 = {}
        formatted2 = {}
        for relation, QEPNodes in self.relationSpecificOperations1.items():
            for QEPNode in QEPNodes:
                formatted1.setdefault(relation, []).append(QEPNode)
        for relation, QEPNodes in self.relationSpecificOperations2.items():
            for QEPNode in QEPNodes:
                formatted2.setdefault(relation, []).append(QEPNode)
        return json.dumps(formatted1, indent=4)#, json.dumps(formatted2, indent=4)
  
    def _getRelationSpecificOperations(self, QEPTree):
        if QEPTree == None:
            return
        relationSpecificOperations = {}
        leafNodes = QEPTree.leaf_nodes #list

        for leafNode in leafNodes:
            relationSpecificOperations[leafNode.relation_name] = [leafNode]
            current = leafNode
            while current.parent != None:
                current = current.parent
                relationSpecificOperations[leafNode.relation_name].append(current)
                
        return relationSpecificOperations
    
    def _checkIfRelationsSame(self):
        """
        To be called within the main comparison method
        """
        difference = []
        for relation in self.relationSpecificOperations1.keys():
            if self.relationSpecificOperations2.get(relation) == None:
                difference.append((relation, 1))
        for relation in self.relationSpecificOperations2.keys():
            if self.relationSpecificOperations1.get(relation) == None:
                difference.append((relation, 2))
        
        grouped = {}
        for item in difference:
            grouped.setdefault(item[1], []).append(item[0])
        
        if len(difference) == 0:
            return "Both QEPs involve the same relations"
        
        returnstr = ""
        if 1 in grouped:
            returnstr += f"{', '.join(grouped[1])} exist in QEP1 but not in QEP2."
        if 2 in grouped:
            returnstr += f"{', '.join(grouped[2])} exist in QEP2 but not in QEP1."
        return returnstr, grouped
    
    def _getJoinConditions(self, QEPTree):
        joinDictionary = {}
        for intermediateName, value in QEPTree.intermediates.items():
            cond = value['formedbyQEP'].hash_cond 
            if cond is not None:
                eachCond = [s.strip().replace("AND", "") for s in cond.split("AND")]
                for item in eachCond:
                    regex = r"(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)"
                    matches = re.findall(regex, str(item))
                    r1, c1, r2, c2 = matches[0]
                    relationlist = [r1, r2]
                    relationlist.sort()
                    condlist = [c1, c2]
                    condlist.sort()
                    joinDictionary[str(relationlist[0]) + ' + ' + str(relationlist[1])] = {
                        #'joinsWith': r2,
                        'key': str(condlist[0]) + ' = ' + str(condlist[1])
                    }

                
        return joinDictionary
    
    def compareIntermediates(self):
        difference = []
        leafplan1 = copy.deepcopy(self.QEPTree1.leaf_plans)
        leafplan2 = copy.deepcopy(self.QEPTree2.leaf_plans)
        if set(leafplan1.keys()) != set(leafplan2.keys()):
            diff1 = list(set(leafplan1.keys()) - set(leafplan2.keys()))
            diff2 = list(set(leafplan2.keys()) - set(leafplan1.keys()))
            temp1 = "Scans in QEP1 that are not present in QEP2 are: "
            temp2 = "Scans in QEP2 that are not present in QEP1 are: "
            if len(diff1) != 0:
                for relation in diff1:
                    temp1 += "{} on {}, ".format(leafplan1[relation], relation)
                    del leafplan1[relation]
                difference.append(temp1)
            if len(diff2) != 0:
                for relation in diff2:
                    temp2 += "{} on {}, ".format(leafplan2[relation], relation)
                    del leafplan2[relation]
                difference.append(temp2)
        # elif set(leafplan1.keys()) == set(leafplan2.keys()):
            for relation in leafplan1.keys():
                if leafplan1[relation] == leafplan2[relation]:
                    continue
                else:
                    difference.append("Scan on {} evolved from {} in QEP1 to {} in QEP2".format(relation, leafplan1[relation], leafplan2[relation]))
        else:
            for relation in leafplan1.keys():
                if leafplan1[relation] == leafplan2[relation]:
                    continue
                else:
                    difference.append("Scan on {} evolved from {} in QEP1 to {} in QEP2".format(relation, leafplan1[relation], leafplan2[relation]))
        if len(difference) == 0:
            difference.append("Both QEPs involve same scan method for each relation")
        print(difference)
        intermediate1 = self._parseIntermediates(self.QEPTree1)
        intermediate2 = self._parseIntermediates(self.QEPTree2)
        #compare
        inBoth = []
        inInt1 = []
        inInt2 = []
        bothJoinString = "{} were joined using {} in both Queries. However, in Query 1 they were joined {} on {}, while in Query 2 they were joined {} on {}"
        totalRelationPairs = set()
        totalRelationPairs.update(intermediate1.keys())
        totalRelationPairs.update(intermediate2.keys())
        for relationPair in totalRelationPairs:
            if relationPair in intermediate1.keys():
                int1 = intermediate1[relationPair]
                if relationPair in intermediate2.keys():
                    int2 = intermediate2[relationPair]
                    # Relation pair is in both intermediates
                    if int1.node_type != int2.node_type:
                        if self.joinDictionary1.get(relationPair) != None:
                            if self.joinDictionary2.get(relationPair) != None:
                                inBoth.append("{} which were originally joined {} using {} in Query 1, are now joined {} using {} in Query 2.".format(relationPair.title(), "directly", int1.node_type, "directly", int2.node_type))
                            else:
                                inBoth.append("{} which were originally joined {} using {} in Query 1, are now joined {} using {} in Query 2.".format(relationPair.title(), "directly", int1.node_type, "indirectly", int2.node_type))
                        else:
                            if self.joinDictionary2.get(relationPair) != None:
                                inBoth.append("{} which were originally joined {} using {} in Query 1, are now joined {} using {} in Query 2.".format(relationPair.title(), "indirectly", int1.node_type, "directly", int2.node_type))
                            else:
                                inBoth.append("{} which were originally joined {} using {} in Query 1, are now joined {} using {} in Query 2.".format(relationPair.title(), "indirectly", int1.node_type, "indirectly", int2.node_type))
                    elif int1.node_type == "Hash Join":
                        if int1.hash_cond != int2.hash_cond:
                            if self.joinDictionary1.get(relationPair) != None:
                                if self.joinDictionary2.get(relationPair) != None:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Hash Join", "directly", int1.hash_cond, "directly", int2.hash_cond))
                                else:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Hash Join", "directly", int1.hash_cond, "indirectly", int2.hash_cond))
                            else:
                                if self.joinDictionary2.get(relationPair) != None:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Hash Join", "indirectly", int1.hash_cond, "directly", int2.hash_cond))
                                else:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Hash Join", "indirectly", int1.hash_cond, "indirectly", int2.hash_cond))
                    elif int1.node_type == "Merge Join":
                        if int1.merge_condition != int2.merge_condition:
                            if self.joinDictionary1.get(relationPair) != None:
                                if self.joinDictionary2.get(relationPair) != None:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Merge Join", "directly", int1.merge_condition, "directly", int2.merge_condition))
                                else:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Merge Join", "directly", int1.merge_condition, "indirectly", int2.merge_condition))
                            else:
                                if self.joinDictionary2.get(relationPair) != None:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Merge Join", "indirectly", int1.merge_condition, "directly", int2.merge_condition))
                                else:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Merge Join", "indirectly", int1.merge_condition, "indirectly", int2.merge_condition))
                    elif int1.node_type == "Nested Loop":
                        if int1.hash_cond != int2.hash_cond:
                            if self.joinDictionary1.get(relationPair) != None:
                                if self.joinDictionary2.get(relationPair) != None:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Nested Loop Join", "directly", int1.hash_cond, "directly", int2.hash_cond))
                                else:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Nested Loop Join", "directly", int1.hash_cond, "indirectly", int2.hash_cond))
                            else:
                                if self.joinDictionary2.get(relationPair) != None:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Nested Loop Join", "indirectly", int1.hash_cond, "directly", int2.hash_cond))
                                else:
                                    inBoth.append(bothJoinString.format(relationPair.title(), "Nested Loop Join", "indirectly", int1.hash_cond, "indirectly", int2.hash_cond))
                else:
                    # Only in intermediate1
                    inInt1.append("A direct join on {} using {} only occurs in Query 1. ".format(relationPair.title(), int1.node_type))
            else:
                # Only in intermediate2
                int2 = intermediate2[relationPair]
                inInt2.append("A join on {} using {} only occurs in Query 2. ".format(relationPair.title(), int2.node_type))

        if len(inBoth) != 0:
            finalComparisonString = "The following relations were joined in both Query 1 and 2, but were either joined using a different join algorithm or on different join conditions:"
            difference.append(finalComparisonString)
            difference.extend(inBoth)
        if len(inInt1) != 0:
            finalComparisonString = "The following differences that occurred are the result of a join on two relations occuring in Query 1 but not in Query 2:"
            difference.append(finalComparisonString)
            difference.extend(inInt1)
        if len(inInt2) != 0:
            finalComparisonString = "The following differences that occurred are the result of a join on two relations occuring in Query 2 but not in Query 1:"
            difference.append(finalComparisonString)
            difference.extend(inInt2)
        return difference  
   
    def _parseIntermediates(self, QEPTree):
        def __checkWhetherRawRelations(relationList):
            if relationList[0].startswith('_') or relationList[1].startswith('_'):
                return False
            return True


        intermediates = QEPTree.intermediates
        intermediateAccumulative = {key: [] for key in intermediates}
        pairDictionary = {}
        relationsInvolved = QEPTree.leaf_plans.keys()
        relationPairs = itertools.combinations(relationsInvolved, 2)        
        for pair in relationPairs:
            sorted_pair = ' + '.join(sorted(pair))
            if sorted_pair not in pairDictionary:
                pairDictionary[sorted_pair] = None
        # print(intermediates)
        for key, value in intermediates.items():
            #when intermediate both from raw relation
            #when intermediate both from intermediates
            print(type(value['formedbyQEP']))
            added = []
            if len(value['formedbyRelations']) == 2:
                if not __checkWhetherRawRelations(value['formedbyRelations']):
                    for i in range(2):
                        if value['formedbyRelations'][i].startswith('_'):
                            toAdd = intermediateAccumulative[value['formedbyRelations'][i]]
                            intermediateAccumulative[key] += toAdd
                        else:
                            toAdd = [value['formedbyRelations'][i]]
                            intermediateAccumulative[key] += toAdd
                        
                        added.append(toAdd)
                else:
                    for relation in value['formedbyRelations']:
                        intermediateAccumulative[key] += [relation]
                        added.append([relation])
                
                for outerRelation in added[0]:
                    for innerRelation in added[1]:
                        if outerRelation != innerRelation:
                            relations = sorted([outerRelation, innerRelation])
                            pairDictionary[relations[0] + " + " + relations[1]] = value['formedbyQEP']
                
            else: #when formedbyrelation only has 1 relation
                if value['formedbyRelations'][0].startswith('_'):
                    intermediateAccumulative[key] += intermediateAccumulative[value['formedbyRelations'][0]]
                else:
                    intermediateAccumulative[key] += [value['formedbyRelations'][0]]
        return pairDictionary
        
        
    def compareMain(self):
        return self.compareIntermediates()
            
            
            
def __checkWhetherRawRelations(relationList):
    if relationList[0].startswith('_') or relationList[1].startswith('_'):
        return False
    return True
                
                
    
                    
                    
    
                    
                
            
        