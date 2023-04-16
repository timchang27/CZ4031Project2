import psycopg2
import json
import qepGenerator
import comparisonGenerator
import logging

class interface(object):
    def __init__(self, con, query1, query2):
        self.con = con
        self.query1 = f"EXPLAIN (ANALYZE false, SETTINGS true, FORMAT JSON) {query1};"
        self.query2 = f"EXPLAIN (ANALYZE false, SETTINGS true, FORMAT JSON) {query2};"
    
    def getComparison(self):
        cursurobject = self.con.cursor()
        cursurobject.execute(self.query1)
        result1 = cursurobject.fetchall()
        logging.info(result1)
        jsonResult1 = json.dumps(result1)
        jsonObject = json.loads(jsonResult1)
        root1 = jsonObject[0][0]
        generatedRoot1 = qepGenerator.extract_from_json(root1)
        QEPTree1 = qepGenerator.QEPTree(generatedRoot1)
        
        cursurobject.execute(self.query2)
        result2 = cursurobject.fetchall()
        jsonResult2 = json.dumps(result2)
        jsonObject2 = json.loads(jsonResult2)
        root2 = jsonObject2[0][0]
        generatedRoot2 = qepGenerator.extract_from_json(root2)
        QEPTree2 = qepGenerator.QEPTree(generatedRoot2)
        
        cg = comparisonGenerator.comparisonGeneartor(QEPTree1, QEPTree2)
        comparisonResult = cg.compareMain()
        return comparisonResult