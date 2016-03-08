#! /usr/bin/python

from suds import client, TypeNotFound

DEFAULT_URL="http://docs.virtualsolar.org/WSDL/VSOi_rpc_literal.wsdl"
DEFAULT_PORT="nsoVSOi"


class QueryResponse(list):
    def __init__(self, lst, queryresult=None):
        super(QueryResponse, self).__init__(lst)
        self.queryresult = queryresult
        self.errors = []
    
    @classmethod
    def create(cls, queryresult):
        return cls(iter_records(queryresult), queryresult)
    
    def total_size(self):
        """ Total size of data in KB. May be less than the actual
        size because of inaccurate data providers. """
        # Warn about -1 values?
        return sum(record.size for record in self if record.size > 0)
    
    def num_records(self):
        """ Return number of records. """
        return len(self)
    
    def time_range(self):
        """ Return total time-range all records span across. """
        return (
            datetime.strptime(
                min(record.time.start for record in self), TIMEFORMAT),
            datetime.strptime(
                max(record.time.end for record in self), TIMEFORMAT)
        )

    def show(self):
        """Print out human-readable summary of records retreived"""

        table = [[str(datetime.strptime(record.time.start, TIMEFORMAT)), 
          str(datetime.strptime(record.time.end, TIMEFORMAT)), 
          record.source,
          record.instrument,
          record.extent.type] for record in self]
        table.insert(0, ['----------','--------','------','----------','----'])        
        table.insert(0, ['Start time','End time','Source','Instrument','Type'])

        print(print_table(table, colsep = '  ', linesep='\n'))
            
    def add_error(self, exception):
        self.errors.append(exception)


class vsoClient(object):
    
    def __init__(self,api=None):
        if not (api):
            api = client.Client(DEFAULT_URL)
            api.set_options(port=DEFAULT_PORT)
        self.api = api

    def make(self, type_, **kwargs):
        obj = self.api.factory.create(type_)
        for k, v in kwargs.iteritems():
            split = k.split('__')
            tip = split[-1]
            rest = split[:-1]
            
            item = obj
            for elem in rest:
                item = item[elem]
            
            if isinstance(v, dict):
                # Do not throw away type information for dicts.
                for k, v in v.iteritems():
                    item[tip][k] = v
            else:
                item[tip] = v
        return obj

    def query(self, *query):
        query = and_(*query)
        
        responses = []
        for block in walker.create(query, self.api):
            try:
                responses.append(
                    self.api.service.Query(
                        self.make('QueryRequest', block=block)
                    )
                )
            except TypeNotFound:
                pass
            except Exception as ex:
                response = QueryResponse.create(self.merge(responses))
                response.add_error(ex)
        
        return QueryResponse.create(self.merge(responses))


