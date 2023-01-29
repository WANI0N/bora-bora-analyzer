import pymongo
import math, threading
from datetime import datetime, timedelta

from functions import get_date_range, calculate_day, convert_date_string_to_obj

class MongoDatabase:
    def __init__(self, db):
        self.db = db
        self.dbIds = list()
        self.dbIds = self.db.products.find({},{"id":1}).distinct('id')
    
    def update_day(self, upload_db: list, thread_count: int = 5):
        if 'date' not in upload_db[0]['history'][0]:
            raise ValueError('invalid upload_db')
        
        upload_db_date = upload_db[0]['history'][0]['date']
        if self.db.products.find_one(
            {'history.0.end-date': upload_db_date},{'id': 1}):
            raise ValueError(f"database already contains {upload_db_date} data")
            
        self.load_latest_record_bulk([o['id'] for o in upload_db])
        self.upload_thread_product_total = len(upload_db)
        self.upload_thread_product_count = 0
        thread_payload = math.floor(len(upload_db)/thread_count)
        padding = len(upload_db) % thread_payload
        threads = []
        for i in range(thread_count):
            start_index = i*thread_payload
            end_index = start_index+thread_payload
            if (i == thread_count-1):
                end_index += padding
            t = threading.Thread(
                target=self.execute_upload_thread,
                args=[upload_db[start_index:end_index], i])
            t.start()
            print(f"thread started-> {str(start_index)}-{str(end_index)}")
            threads.append(t)
        for i, thread in enumerate(threads):
            thread.join()
    
    def execute_upload_thread(self, products, thread_index):
        for product in products:
            if self.upload_thread_product_count % 500 == 0:
                print(f"{self.upload_thread_product_count} out of {self.upload_thread_product_total}")
            self.upload_thread_product_count += 1
            input_day_record = {
                'end-date': product['history'][0]['date'],
                'start-date': product['history'][0]['date'],
                'availability': [product['history'][0]['active']],
                'price': product['history'][0]['price'],
                'comparative_unit_price': product['history'][0]['comparative_unit_price'],
            }
            if product['id'] in self.dbIds:
                latest_day = self.latest_record_bulk[product['id']]['history'][0]
                new_availability = input_day_record['availability'] + latest_day['availability']
                
                if latest_day['price'] == input_day_record['price'] and \
                    calculate_day(input_day_record['start-date'], -1) == latest_day['end-date']:
                    assert len(get_date_range(input_day_record['end-date'], latest_day['start-date'])) == \
                        len(new_availability), f"assertion error on f{product['id']}"
                    
                    self.db.products.update_one({'id': product['id']},{
                                                "$set":{   
                                                    "history.0.end-date": 
                                                        input_day_record['end-date'],
                                                    'history.0.availability':
                                                        new_availability,
                                                    "image": 
                                                        product['image'],
                                                }})
                    continue
                else:
                    self.db.products.update_one(
                        {'id': product['id']},
                        {"$push": {"history": {
                            "$each": [input_day_record],
                            "$position": 0
                        }},"$set": {"image": product['image']}})
            else: #create new item
                product['history'][0] = input_day_record
                self.db.products.insert_one( product )
        print("thread #" + str(thread_index) + " finished")
    
    def get_daycount_subtract_str_dateObj(self, date_string: str, date_object: datetime) -> int:
        d0 = convert_date_string_to_obj(date_string)
        return (d0 - date_object).days
    
    def trim_db_submit(self, limit: int = 365) -> None:
        last_included_date_string = (datetime.now()-timedelta(days = limit)).strftime("%Y-%m-%d")
        self.trim_db_to_date(last_included_date_string)
    
    def trim_db_to_date(self, cutoff_datestring_incl: str) -> None:
        if len(cutoff_datestring_incl) != 10:
            print(f"invalid date: {cutoff_datestring_incl}")
            return
        if cutoff_datestring_incl[4] != "-" or cutoff_datestring_incl[7] != "-":
            print(f"invalid date: {cutoff_datestring_incl}")
            return
        
        batch_size = 200
        self.load_oldest_record_bulk()
        array = cutoff_datestring_incl.split("-")
        cutoff_date_object = datetime(int(array[0]), int(array[1]), int(array[2]))
        
        products_to_pop = []
        products_to_update = set()
        modified_products_count = 0
        for record in self.oldest_record_bulk:
            last_record = record['history'][0]
            day_count_diff = self.get_daycount_subtract_str_dateObj(
                last_record['start-date'],
                cutoff_date_object
            )
            if day_count_diff < 0:
                modified_products_count += 1
                if last_record['end-date'] == last_record['start-date'] \
                    or self.get_daycount_subtract_str_dateObj(
                        last_record['end-date'], 
                        cutoff_date_object) < 0:
                    products_to_pop.append(record['id'])
                else:
                    _key = f"{last_record['start-date']}_{abs(day_count_diff)}"
                    if _key not in products_to_update:
                        products_to_update.add(_key)
        
        print('execuing mass trim update...')
        for k in products_to_update:
            arr = k.split('_')
            start_date = arr[0]
            pop_count = int(arr[1])
            print(f"execuing mass trim update: {start_date} -{pop_count}")
            self.db.products.update_many({   
                    'history.start-date': start_date,
                },{"$set": {
                    "history.$.start-date": cutoff_datestring_incl,
                    },
                    "$pop": {"history.$.availability": pop_count}
                })
        
        print('execuing mass pop update...')
        loop_count = math.floor(len(products_to_pop)/batch_size)
        padding = len(products_to_pop) % batch_size
        for i in range(loop_count):
            start_index = i*batch_size
            end_index = start_index+batch_size
            if (i == loop_count-1):
                end_index += padding
            print(f'execuing mass pop update... {i}/{loop_count}')
            self.db.products.update_many(
                {"id": {"$in": products_to_pop[start_index:end_index]}},
                {"$pop": { 'history': 1 }})
                    
        #deleting products with no history
        print("starting bulk delete many")
        ids_to_delete = []
        deleted_products_count = 0
        for product in self.db.products.find({'history': {'$size': 0}}, {'id': 1 }):
            ids_to_delete.append(product['id'])
            deleted_products_count += 1
            if len(ids_to_delete) == batch_size:
                print(f"executing bulk delete many -> {len(ids_to_delete)}")
                self.db.products.delete_many({"id": {"$in": ids_to_delete}})
                ids_to_delete = []
        if ids_to_delete:
            print(f"executing bulk delete many -> {len(ids_to_delete)}")
            self.db.products.delete_many({"id": {"$in": ids_to_delete}})
        
        print(f"trim_db_to_date finished: modified={modified_products_count} deleted={deleted_products_count}")
    
    def load_latest_record_bulk(self, target_ids: list):
        self.latest_record_bulk = {}
        batch_size = 500
        loop_count = math.floor(len(target_ids)/batch_size)
        dbSubmit_padding = len(target_ids) % batch_size
        print('pulling latest_record_bulk...')
        for i in range(loop_count):
            start_index = i*batch_size
            print(f'pulling latest_record_bulk... {start_index}/{len(target_ids)}')
            end_index = start_index+batch_size
            if (i == loop_count-1):
                end_index += dbSubmit_padding
            products = self.db.products.find(
                {"id": {"$in": target_ids[start_index:end_index]}},
                {'history': {'$slice': [0, 1]}, "id": 1},
                batch_size=batch_size)
            products = list(products)
            for prod in products:
                del prod['_id']
                self.latest_record_bulk[prod['id']] = prod
        print('latest_record_bulk pulled')
            
    def load_oldest_record_bulk(self):
        self.oldest_record_bulk = []
        batch_size = 500
        loop_count = math.floor(len(self.dbIds)/batch_size)
        dbSubmit_padding = len(self.dbIds) % batch_size
        print('pulling oldest_record_bulk...')
        for i in range(loop_count):
            start_index = i*batch_size
            print(f'pulling oldest_record_bulk... {start_index}/{len(self.dbIds)}')
            end_index = start_index+batch_size
            if (i == loop_count-1):
                end_index += dbSubmit_padding
            products = self.db.products.find(
                {"id": {"$in": self.dbIds[start_index:end_index]}},
                {'history': {'$slice': -1}, "id": 1},
                batch_size=batch_size)
            products = list(products)
            for prod in products:
                del prod['_id']
                self.oldest_record_bulk.append(prod)
                # self.oldest_record_bulk[prod['id']] = prod
        print('oldest_record_bulk pulled')

    def clean_user_alerts(self):
        # drop deleted products from user alerts
        print('starting clean_user_alerts')
        for user in self.db.user.find(
            {"validation_status": True},
            {"alerts": 1, "id_cookie": 1}):
            print(f"checking user: {user['id_cookie']}...")
            if 'alerts' not in user:
                continue
            alert_ids = [alert['productID'] for alert in user['alerts']]
            existing_products_ids = []
            for prod in self.db.products.find({"id": {"$in": alert_ids}}, {"id": 1}):
                existing_products_ids.append(prod['id'])
            if len(existing_products_ids) < len(alert_ids):
                print(f"removing {len(alert_ids)-len(existing_products_ids)} products alerts")
                new_alerts = []
                for alert in user['alerts']:
                    if alert['productID'] in existing_products_ids:
                        new_alerts.append(alert)
                self.db.user.update_one(
                    {"id_cookie": user["id_cookie"]},
                    {"$set": {"alerts": new_alerts}})


if __name__ == "__main__":
    from webcrawler import BarboraCrawler
    import certifi, os, json
    from dotenv import load_dotenv
    ca = certifi.where()
    load_dotenv()
    DATABASE_URL=f'mongodb+srv://{os.environ.get("DB_NAME_2")}:{os.environ.get("DB_PASSWORD_2")}'\
        '@cluster0.ichgboc.mongodb.net/?retryWrites=true&w=majority'
    client=pymongo.MongoClient(DATABASE_URL,tlsCAFile=ca) # establish connection with database
    mongo_db_2=client.db
    
    # crawler = BarboraCrawler()
    # crawler.analyze()
    # crawler.outputDatabase()
    
    db_handler = MongoDatabase(mongo_db_2)
    # db_handler.trim_db_to_date('2022-01-22')
    # db_handler.trim_db_submit()
    # db_handler.update_day(crawler.database)
    # with open('2023-01-26.json', 'r') as f:
    #     crawler_db = json.loads(f.read())
    # db_handler.update_day(crawler_db)
    # db_handler.clean_user_alerts()
    
    # db_handler.create_edge_record_bulk()
    