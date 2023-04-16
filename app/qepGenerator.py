import json
import copy
import string
import os
import queue


class QEPnode(object):
    def __init__(self, idx, type, join_type, startup_cost, total_cost, plan_rows, hash_cond, relation_name,
        group_key, sort_key, index_name, table_filter, index_condition, merge_condition, join_filter):
        self.idx = idx
        self.node_type = type  #
        self.children = []
        self.parent = None
        self.join_type = join_type  #
        self.startup_cost = startup_cost
        self.total_cost = total_cost
        self.plan_rows = plan_rows
        self.hash_cond = hash_cond      #
        self.relation_name = relation_name
        self.group_key = group_key      #
        self.sort_key = sort_key        #
        self.index_name = index_name    #
        self.table_filter = table_filter #
        self.index_condition = index_condition  #
        self.merge_condition = merge_condition  #
        self.join_filter = join_filter
        self.formsIntermediate = None
    
    def append_children(self, child):
        self.children.append(child)
        
    def _checkIfOnlyChild(self):
        """
        @params: None
        Checks if the current node is the only child of his parent node, if parent exists
        Returns a boolean
        """
        if self.parent == None: #indicates root node
            return False
        
        if len(self.parent.children) == 1:
            return True
        
        return False
                
        
    # def __repr__(self):
    #     if self.parent == None:
    #         parent_idx = -99
    #     else:
    #         parent_idx = self.parent.idx
        
    #     return f"QEPnode(idx = '{self.idx}', parent='{parent_idx}', type='{self.node_type}', join_type='{self.join_type}', formsIntermediate='{self.formsIntermediate}')"
    # def __repr__(self):
    #     attrs = {}
    #     for k, v in self.__dict__.items():
    #         if v is not None:
    #             attrs[k] = v
    #     return f"{type(self).__name__}({', '.join(f'{k}={v!r}' for k, v in attrs.items())})"
    def __repr__(self):
        return f"QEPnode(idx={self.idx}, type={self.node_type}, join_type={self.join_type}, " \
               f"hash_cond={self.hash_cond}, relation_name={self.relation_name}, group_key={self.group_key}, " \
               f"sort_key={self.sort_key}, index_name={self.index_name}, table_filter={self.table_filter}, " \
               f"index_condition={self.index_condition}, merge_condition={self.merge_condition}, " \
               f"join_filter={self.join_filter})"
    
    
class QEPTree(object):
    def __init__(self, root_node):
        self.root_node = root_node
        self.leaf_nodes = []
        self.leaf_plans = {}
        self.intermediates = {}
        self.intermediatesCounter = 0
        self.nodeTypeToSkip = ['Gather', 'Gather Merge', 'Materialize', 'Limit']
        # {'T1': {
        #     formed: ['nation'],
        #     description: 'some string - aggregated on something'
        # }
        # 'T2': {
        #     formed: ['part'],
        #     description: 'hashed on some key'
        # },
        # 'T3': {
        #     formed: ['T1', 'T2']
        #     description: 'hash joined'
        # } 
        #  }
        self._extractLeafNodes()
        self._extractLeafPlans()
        self._setParentRecursive(self.root_node)
        self._generateIntermediatesPostOrder(self.root_node)
        
    def _extractLeafNodes(self):
        child_queue = queue.Queue()
        for child in self.root_node.children:
            child_queue.put(child)
            
        while not child_queue.empty():
            current = child_queue.get()
            if len(current.children) != 0:
                for currentchild in current.children:
                    child_queue.put(currentchild)
            else:
                self.leaf_nodes.append(current)
                                
    def _extractLeafPlans(self):
        leaf_plans = {}
        for node in self.leaf_nodes:
            leaf_plans[node.relation_name] = node.node_type
        self.leaf_plans = leaf_plans
        return leaf_plans
        
    def _setParentRecursive(self, root, parent = None): #to be called upon instantiation
        if root == None:
            return
        
        root.parent = parent
        
        if len(root.children) == 2:
            self._setParentRecursive(root.children[0], root)
            self._setParentRecursive(root.children[1], root)
        elif len(root.children) == 1:
            self._setParentRecursive(root.children[0], root)
        else:
            self._setParentRecursive(None)
            
    def _generateIntermediatesPostOrder(self, root_node):
        def _checkChildRelationName(node):
            if node.relation_name == None:
                return node.formsIntermediate, node.idx
            return node.relation_name, node.idx
        
        def _checkChildToSkip(node):
            """Recursively check whether the child's node type is Gather or Materialise or Gather Merge
                If the child node belongs to one of the node type above, resursively call this funciton again
                Else Return the QEPNode
            Args:
                node (QEPNode): QEPNode
            """
            if len(node.children) == 0: #Terminator
                return node
            node_type = node.children[0].node_type
            if node_type in self.nodeTypeToSkip:
                return _checkChildToSkip(node.children[0])
            else:
                return node.children[0]
            
        def _checkChildToSkip2(node):
            if len(node.children) == 0:
                return node
            node_type1 = node.children[0].node_type
            node_type2 = node.children[1].node_type
            if node_type1 in self.nodeTypeToSkip:
                actualChildNode1 = _checkChildToSkip(node.children[0])
            else:
                actualChildNode1 = node.children[0]
            if node_type2 in self.nodeTypeToSkip :
                actualChildNode2 = _checkChildToSkip(node.children[1])
            else:
                actualChildNode2 = node.children[1]
            
            return actualChildNode1, actualChildNode2
                
        
        #Traverse bottom up from the leaf nodes
        if root_node == None:
            return
        
        # if len(root_node.children) == 2:
        #     self._generateIntermediatesPostOrder(root_node.children[0])
        #     self._generateIntermediatesPostOrder(root_node.children[1])
        #     #2 children nodes - confirm forming some intermediate
        #     table0, idx0 = _checkChildRelationName(root_node.children[0])
        #     table1, idx1 = _checkChildRelationName(root_node.children[1])
        #     root_node.formsIntermediate = 'T' + str(self.intermediatesCounter)#str(table0) + ' + ' + str(table1)
        #     self.intermediatesCounter += 1
        #     intermediateDict = { 
        #                             'formedbyRelations': [table0, table1],
        #                             'formedFromQEPidx': [idx0, idx1],
        #                             'formedbyQEP': root_node.__repr__()
        #                         }
        #     self.intermediates[root_node.formsIntermediate] = intermediateDict
            
            
        # elif len(root_node.children) == 1:
        #     self._generateIntermediatesPostOrder(root_node.children[0])
        #     #some code
        #     print('checking skip nodes of children of: ', root_node.idx)
        #     actualChildNode = _checkChildToSkip(root_node)  #after ignoring all the skipped nodes
        #     print('child node extracted is ' , actualChildNode.idx)
        #     table, idx = _checkChildRelationName(actualChildNode)
        #     root_node.formsIntermediate = 'T' + str(self.intermediatesCounter)#str(table) 
        #     self.intermediatesCounter += 1
        #     intermediateDict = {
        #                             'formedbyRelations': [table],
        #                             'formedFromQEPidx': [idx],
        #                             'formedbyQEP': root_node.__repr__()
        #                         }
        #     self.intermediates[root_node.formsIntermediate] = intermediateDict
            
        if len(root_node.children) == 2:
            actualChildNode1, actualChildNode2 = _checkChildToSkip2(root_node)
            self._generateIntermediatesPostOrder(actualChildNode1)
            self._generateIntermediatesPostOrder(actualChildNode2)
            #2 children nodes - confirm forming some intermediate
            table0, idx0 = _checkChildRelationName(actualChildNode1)
            table1, idx1 = _checkChildRelationName(actualChildNode2)
            root_node.formsIntermediate = '_T' + str(self.intermediatesCounter)#str(table0) + ' + ' + str(table1)
            self.intermediatesCounter += 1
            intermediateDict = { 
                                    'formedbyRelations': [table0, table1],
                                    'formedFromQEPidx': [idx0, idx1],
                                    'formedbyQEP': root_node
                                }
            self.intermediates[root_node.formsIntermediate] = intermediateDict
        elif len(root_node.children) == 1:
            actualChildNode = _checkChildToSkip(root_node)  #after ignoring all the skipped nodes
            self._generateIntermediatesPostOrder(actualChildNode)
            #actualChildNode = _checkChildToSkip(root_node)  #after ignoring all the skipped nodes
            table, idx = _checkChildRelationName(actualChildNode)
            root_node.formsIntermediate = '_T' + str(self.intermediatesCounter)#str(table) 
            self.intermediatesCounter += 1
            intermediateDict = {
                                    'formedbyRelations': [table],
                                    'formedFromQEPidx': [idx],
                                    'formedbyQEP': root_node
                                }
            self.intermediates[root_node.formsIntermediate] = intermediateDict

        else:
            self._generateIntermediatesPostOrder(None)
            
        #implement the insertion into intermediate dictionary
    
    def getIntermediates(self):
        return self.intermediates
    
    def printIntermediates(self):
        for key, value in self.intermediates.items():
            print()
      
    def __repr__(self):
        toreturn = ""
        child_queue = queue.Queue()
        child_queue.put(self.root_node)
        while not child_queue.empty():
            cur = child_queue.get()
            toreturn += (cur.__repr__() + "\n")
            if len(cur.children) != 0:
                for child in cur.children:
                    child_queue.put(child)
                    
        return toreturn
            
        
            
            
    
    
    
        
        

def extract_from_json(json_obj):
    child_queue = queue.Queue()
    parent_queue = queue.Queue()
    root = json_obj[0]['Plan']
    child_queue.put(root)
    parent_queue.put(None)
    idx = 0
    rootInitialised = False
    
    while not child_queue.empty():
        current_node = child_queue.get()
        parent_node = parent_queue.get()
        
        if current_node.get('Node Type', -1) != -1: 
            node_type = current_node['Node Type'] 
        else:
            node_type = None
            
        if current_node.get('Join Type', -1) != -1: 
            join_type = current_node['Join Type']
        else: 
            join_type = None
        
        if current_node.get('Startup Cost', -1) != -1: 
            startup_cost = current_node['Startup Cost']
        else:
            startup_cost = None
        
        if current_node.get('Total Cost', -1) != -1: 
            total_cost = current_node['Total Cost']
        else:
            total_cost = None
        
        if current_node.get('Plan Rows', -1) != -1: 
            plan_rows = current_node['Plan Rows']
        else:
            plan_rows = None
        
        if current_node.get('Hash Cond', -1) != -1: 
            hash_cond = current_node['Hash Cond']
        else:
            hash_cond = None
            
        if current_node.get('Relation Name', -1) != -1: 
            relation_name = current_node['Relation Name']
        else:
            relation_name = None
            
        if current_node.get('Group Key', -1) != -1: 
            group_key = current_node['Group Key']
        else:
            group_key = None    
            
        if current_node.get('Sort Key', -1) != -1: 
            sort_key = current_node['Sort Key']
        else:
            sort_key = None
        
        if current_node.get('Index Name', -1) != -1: 
            index_name = current_node['Index Name']
        else:
            index_name = None
    
        if current_node.get('Table Filter', -1) != -1: 
            table_filter = current_node['Table Filter']
        else:
            table_filter = None
            
        if current_node.get('Index Cond', -1) != -1: 
            index_condition = current_node['Index Cond']
        else:
            index_condition = None
        
        if current_node.get('Merge Cond', -1) != -1: 
            merge_condition = current_node['Merge Cond']
        else:
            merge_condition = None
        
        if current_node.get('Join Filter', -1) != -1: 
            join_filter = current_node['Join Filter']
        else:
            join_filter = None            
        
                
        new_node = QEPnode(idx, node_type, join_type, startup_cost, total_cost, plan_rows, hash_cond, relation_name,
        group_key, sort_key, index_name, table_filter, index_condition, merge_condition, join_filter)
        
        idx += 1
        
        if parent_node is not None:
            parent_node.append_children(new_node)
        else:
            root_node = new_node
        
        if 'Plans' in current_node:
            for item in current_node['Plans']:
                child_queue.put(item)
                parent_queue.put(new_node)
                
    return root_node
        
    
    if root.get('Nddode Type', None) != None:
        print(len(root['Plans']))
