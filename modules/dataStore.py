import os
import sqlite3

class dataStore():
    '''
    This class provides the data storage and retrieval interface.
    
    Usage:
    # data store location
    location = '../someLocation/database.db'
    
    # columns of your choice (digits in column names are not supported)
    columns = ('name','columnA','columnB')
    
    # create data store
    dStore = dataStore(location, columns)
    
    # create new record (duplicate names are not allowed)
    dStore.createRecord('Record1') # create new record 'Record1'
    
    # write data by passing a tuple of positional arguments
    dStore.write(('Record1','columnA data','columnB data'))
    
    # read data by passing the record name
    # returns a list of dictionaries
    result = dStore.readFrom('Record1')
    
    # delete a record by name
    dStore.deleteRecord('Record1')
    '''
    def __init__(self, location, fields):
        self.location = str(location)
        self.fields = fields
        self.head = fields[0]
        self.tail = fields[1:]
        self.connection = None
        self.cursor = None
        
        if not os.path.exists(self.location):
            self.createNewDB()
    
    def createNewDB(self):
        self.connect()
        self.execute( "CREATE TABLE Pockets ({f} TEXT NOT NULL UNIQUE)"\
                      .format(f=self.head) )
        for field in self.tail:
            self.execute( "ALTER TABLE Pockets ADD COLUMN {f} TEXT"\
                          .format(f=field) )

    def connect(self):
        self.connection = sqlite3.connect(self.location)
        self.connection.isolation_level = None # auto-commit mode
        self.cursor = self.connection.cursor()
        
    def disconnect(self):
        self.connection.close()

    def execute(self, command):
        self.cursor.execute(command)

    def createRecord(self, name):
        try:
            self.execute( "INSERT INTO Pockets ({f}) VALUES ('{n}')"\
                          .format(f=self.head, n=name) )
            return True
        except:
            return False # contains illegal characters or this record already exists
    
    def deleteRecord(self, name):
        try:
            
            self.execute("DELETE FROM Pockets WHERE {f}='{n}'"\
                         .format(f=self.head, n=name) )
            return True
        except:
            print('Could not delete record!')
            return False
    
    def readFrom(self, name):
        data = self.execute("SELECT * FROM Pockets WHERE {f}='{n}'"\
                            .format(f=self.head, n=name) )
        return self.unpackData(data)
    
    def write(self, data):
        pData = self.packData(data)
        for field in self.tail:
            self.execute("UPDATE Pockets SET {key}='{val}' WHERE {f}='{n}'"\
                         .format(key=field, val=pData[field], f=self.head, n=pData[self.head]) )
        
    def getAllData(self):
        self.connect()
        self.execute("SELECT * FROM Pockets")
        data = self.cursor.fetchall()
        return self.unpackData(data)
    
    def unpackData(self, data):
        return [dict(zip(self.fields, pocket)) for pocket in data]
    
    def packData(self, data):
        return dict(zip(self.fields, data))
        