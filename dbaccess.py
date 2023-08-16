import pymongo

if __name__=='__main__':
    dbclient = pymongo.MongoClient('mongodb://localhost:27017/')

    mydb = dbclient['py_data']
    mycol = mydb['py_collection']

    test = {'Name': 'Test1', 'Type':'type1', 'objty':'ty1'}

    mycol.insert_one(test)

    res = mycol.find({'Name': 'Test1'})

    for e in res:
        print(e)
    