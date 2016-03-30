
import re
from gluon import current

class DataTablesServer:
    """Ajax data server for Datatables
    """
    def __init__( self, request, columns, index, collection):
        
        self.columns = columns
        self.index = index
        
        # table - element, branch, category, tag
        self.collection = collection
         
        # values specified by the datatable for filtering, sorting, paging
        self.request_values = request
        
        # results from the db
        self.result_data = None
         
        # total in the table after filtering
        self.cardinality_filtered = 0
        
        # total in the table unfiltered
        self.cadinality = 0
        
        self.run_queries()
        
    def run_queries(self):
        """
        """
        db = current.db
        
        # pages has 'start' and 'length' attributes
        pages = self.paging()
        
        # the term you entered into the datatable search
        filtering = self.filtering()
        
        # the document field you chose to sort
        sorting = self.sorting()
        
        limit = (pages['start'], pages['start'] + pages['length'])
        
        if self.collection == 'element':
            query = (db.xelements_element.category_id==db.xelements_category.id) & \
                    (db.xelements_category.branch_id==db.xelements_branch.id) & \
                    (db.xelements_element.retired==0)
            
            if filtering['or']:
                query &= filtering['or']
            
            self.cardinality_filtered = db(query).count()
            
            rows = db(query).select(limitby=limit, orderby=sorting)
            
        elif self.collection == 'category':
            query = (db.xelements_branch.id==db.xelements_category.branch_id)
            filtered = db(query).select(db.xelements_category.id,
                                        left=db.xelements_element.on(db.xelements_element.category_id==db.xelements_category.id),
                                        groupby=db.xelements_category.id,
                                        )
            self.cardinality_filtered = len(filtered)
            
            if filtering['or']:
                query &= filtering['or']
            
            count = db.xelements_element.id.count()
            rows = db(query).select(db.xelements_branch.id,
                                db.xelements_branch.name,
                                db.xelements_category.id,
                                db.xelements_category.name,
                                db.xelements_category.colour,
                                count,
                                left=db.xelements_element.on(db.xelements_element.category_id==db.xelements_category.id),
                                groupby=db.xelements_category.id,
                                limitby=limit,
                                orderby=sorting,
                                )
            
        elif self.collection == 'branch':
            query = (db.xelements_branch.id>0)
            filtered = db(query).select(db.xelements_branch.id, groupby=db.xelements_branch.id)
            self.cardinality_filtered = len(filtered)
            
            if filtering['or']:
                query &= filtering['or']
                
            count = db.xelements_category.id.count()
            rows = db(query).select(db.xelements_branch.id,
                                    db.xelements_branch.name,
                                    count,
                                    left=db.xelements_category.on(db.xelements_category.branch_id==db.xelements_branch.id),
                                    limitby=limit, orderby=sorting,
                                    groupby=db.xelements_branch.id,
                                    )
            
        elif self.collection == 'tag':
            query = (db.xelements_tag.id>0)
            filtered = db(query).select(db.xelements_tag.id,groupby=db.xelements_tag.id)
            self.cardinality_filtered = len(filtered)
            
            if filtering['or']:
                query &= filtering['or']
            
            count = db.xelements_tagmap.id.count()
            rows = db(query).select(db.xelements_tag.id,
                                    db.xelements_tag.name,
                                    db.xelements_tag.code,
                                    count,
                                    left=db.xelements_tagmap.on(db.xelements_tagmap.tag_id==db.xelements_tag.id),
                                    limitby=limit, orderby=sorting,
                                    groupby=db.xelements_tag.id,
                                    )
            
        else:
            self.result_data = []
            self.cardinality_filtered = 0
            self.cardinality = 0
            return
        
        self.result_data = rows.as_list()
        self.cardinality = len(self.result_data)
        
    def filtering(self):
        """
        """
        db = current.db
        
        pat = re.compile('(\w+)X([\d]*)')
        # build your filter spec
        filter = {'or':None, 'and':None}
        
        if self.request_values.has_key('search[value]'):
            search_val = self.request_values['search[value]']
            if search_val:
                m = pat.match(search_val)
                if m:
                    name = m.group(1)
                    element_code = m.group(2)
                    q = (db.xelements_category.id==db.xelements_element.category_id) & (db.xelements_element.name==name)
                    if element_code:
                        q &= (db.xelements_element.element_code.contains(element_code))
                    filter['or'] = q
                else:
                    # doesn't contain X joiner
                    search_string = '%{0}%'.format(search_val)
                    # the term put into search is logically concatenated with 'or' between all columns
                    or_filter_on_all_columns = None
                    for i in range(len(self.columns)):
                        if self.request_values['columns[{0}][searchable]'.format(i)] == 'false':
                            continue
                        table_name, col_name = self.request_values['columns[{0}][name]'.format(i)].split('.')
                        if or_filter_on_all_columns:
                            or_filter_on_all_columns |= db[table_name][col_name].like(search_string)
                        else:
                            or_filter_on_all_columns = db[table_name][col_name].like(search_string)
                            
                    filter['or'] = or_filter_on_all_columns
        return filter
        
    def sorting(self):
        """
        """
        db = current.db
        
        order_dict = {'asc': 1, 'desc': -1}
        ordering = None
        
        if (self.request_values['order[0][column]'] > -1):
            for i in range(len(self.columns)):
                if not self.request_values.has_key('order[{0}][column]'.format(i)):
                    break
                    
                order_col = int(self.request_values['order[{0}][column]'.format(i)])
                order_dir = self.request_values['order[{0}][dir]'.format(i)]
                
                if self.request_values['columns[{0}][orderable]'.format(order_col)] == 'false':
                    continue
                    
                if self.request_values['columns[{0}][name]'.format(order_col)].startswith('COUNT('):
                    col_name = self.request_values['columns[{0}][name]'.format(order_col)]
                    if ordering:
                        if order_dir == 'asc':
                            ordering |= col_name
                        else:
                            ordering |= '~'+col_name
                    else:
                        if order_dir == 'asc':
                            ordering = col_name
                        else:
                            ordering = '~'+col_name
                            
                else:
                    table_name, col_name = self.request_values['columns[{0}][name]'.format(order_col)].split('.')
                    
                    # element name sorting
                    if table_name == 'xelements_element' and col_name == 'name':
                        if order_dir == 'asc':
                            o = db['xelements_element']['name'] | db['xelements_element']['element_code']
                        else:
                            o = ~db['xelements_element']['name'] | ~db['xelements_element']['element_code']
                        if ordering:
                            ordering |= o
                        else:
                            ordering = o
                    else :
                        if ordering:
                            if order_dir == 'asc':
                                ordering |= db[table_name][col_name]
                            else:
                                ordering |= ~db[table_name][col_name]
                        else:
                            if order_dir == 'asc':
                                ordering = db[table_name][col_name]
                            else:
                                ordering = ~db[table_name][col_name]
                    
        return ordering
        
    def paging(self):
        """
        """
        pages = {'start':0, 'length':0}
        if (self.request_values['start'] != "" ) and (self.request_values['length'] != -1 ):
            pages['start'] = int(self.request_values['start'])
            pages['length'] = int(self.request_values['length'])
        return pages
        
    def output_result(self):
        """
        DT_RowId
        """
        output = {}
        output['draw'] = int(self.request_values['draw'])
        output['recordsTotal'] = self.cardinality
        output['recordsFiltered'] = self.cardinality_filtered
        
        checkbox = '<input type="checkbox" class="dt-checkbox row-checkbox">'
        
        data = []
        
        for row in self.result_data:
            x = self.index.split('.')
            aaData_row = {'DT_RowId':row[x[0]][x[1]]}
            
            for i in range( len(self.columns) ):
                column = self.columns[i].replace('xelements_','').replace('.','_')
                
                if column == 'checkbox':
                    aaData_row[column] = checkbox
                    continue
                
                if self.columns[i].startswith('COUNT('):
                    column = 'count'
                    t = '_extra'
                    c = self.columns[i]
                else:
                    t, c = self.columns[i].split('.') # xelements_element.name
                val = row[t][c]
                
                if t == 'xelements_element' and c == 'name':
                    val = '{0}X{1}'.format(row[t][c], row[t]['element_code'])
                elif c == 'date_updated':
                    if hasattr(val, 'isoformat'):
                        val = val.strftime('%b %d %Y %I:%M %P')
                
                aaData_row[column] = val
                
            data.append(aaData_row)
            
        output['data'] = data
        
        return output
        