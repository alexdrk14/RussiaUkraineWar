from pymongo import MongoClient
from datetime import datetime, timedelta
from os.path import isfile, join
from os import listdir
import subprocess
from collections import defaultdict
import os.path
import dill
import calendar
import config as cnf

data = {}
suspend  = []
deactive = []

def connect_to_db():
  client = MongoClient(cnf.db_ip, cnf.db_port)
  db = client[cnf.db_name]
  return client , db


def set_commas(value)->str:
  final_value = ""
  
  while True:
    left = value % 1000
    value = int((value - left )/ 1000)
    #print("Value{}".format(value))
    if value > 0:
      final_value = (str(left) + "." + final_value)  if len(str(left)) == 3 else "0" + str(left) + "." + final_value
      #print("final:{}".format(final_value))
    else:
      final_value = (str(left)+ "." + final_value) if len(str(left)) == 3 else "0" + str(left) + "." + final_value
      #print("Final:{}".format(final_value))
      break
  while final_value[0] == "0":
    final_value = final_value[1:]
  return final_value[:-1]


def get_db_users_tweets():
  global data
  client , db =  connect_to_db()
  data["users"] = set_commas(int(db[cnf.col_users].count({})))
  data["tweets"] = set_commas(int(db[cnf.col_tweets].count({})))
  client.close()



def get_suspend():
  global data
  global suspend 
  global deactive

  date_obj = datetime.now()
  
  filenames = [join(cnf.compliance_files, f) for f in listdir(cnf.compliance_files) if isfile(join(cnf.compliance_files, f)) and cnf.compliance_prefix in f]
  for file in filenames:
    #print(file)
    date = file.split(cnf.compliance_prefix)[1].split("_")[0].split("-")
    date = (int(date[0]) * 100) + int(date[1]) 
    
    suspend.append( (date, int(subprocess.getoutput("cat {} | grep suspend | wc -l ".format(file)))) )
    deactive.append( (date, int(subprocess.getoutput("cat {} | grep deactivated | wc -l ".format(file)))) )
  
  suspend.sort(key=lambda t:t[0])
  deactive.sort(key=lambda t:t[0])
  
  f_out = open("../data/suspension.csv", "w+")
  f_out.write("date,suspend,deactive\n")
  for i in range(len(suspend)):
    date = suspend[i][0] % 100
    month = calendar.month_name[int((suspend[i][0] - date) / 100)][:3]
    f_out.write("{}-{},{},{}\n".format(month, date, suspend[i][1], deactive[i][1]))
  f_out.close()
  
  suspend = [x[1] for x in suspend]
  deactive = [x[1] for x in deactive]
  data["suspend"] = set_commas(suspend[-1])
  data["deactive"] = set_commas(deactive[-1])


def get_hashtags(tweet):
  hashtags = set()
  element = None
  if "quoted_status" in tweet:
    if "extended_tweet" in tweet["quoted_status"]:
      element = tweet["quoted_status"]["extended_tweet"]
    else:
      element = tweet["quoted_status"]
    
  elif "retweeted_status" in tweet:
    if "extended_tweet" in tweet["retweeted_status"]:
      element = tweet["retweeted_status"]["extended_tweet"]
    else:
      element = tweet["retweeted_status"]
  if element != None:
    for hs in element["entities"]["hashtags"]:
      hashtags.add(hs["text"])
  if "extended_tweet" in tweet:
    element = tweet["extended_tweet"]
  else:
    element = tweet
  for hs in element["entities"]["hashtags"]:
    hashtags.add(hs["text"])
  return hashtags
  

def get_daily_volume():
  
  days = set()
  daily_users = defaultdict(lambda: set())
  daily_tweets = defaultdict(lambda: 0)
  daily_hashtags = defaultdict(lambda: defaultdict(lambda: 0))
  daily_lang = defaultdict(lambda: defaultdict(lambda: 0))


  """If already parsed previous dates, load data and start from the last date"""
  if os.path.exists("../data/pickle_users.dump"):
    f = open("../data/pickle_users.dump","rb")
    daily_users = dill.load(f)
    f.close()
   
    f = open("../data/pickle_tweets.dump","rb")
    daily_tweets = dill.load(f)
    f.close()
   
    f = open("../data/pickle_hashtag.dump","rb")
    daily_hashtags = dill.load(f)
    f.close()
    
    f = open("../data/pickle_lang.dump","rb")
    daily_lang = dill.load(f)
    f.close()
    
    days = set([x for x in daily_users])
    
    last_seen = max(days)
    last_day = last_seen % 100
    last_month = int((last_seen - last_day)/100)
    start_date = datetime(2022, last_month, last_day,0,0,0) + timedelta(days=1) 
   
  else:
    start_date = datetime(2022, 2, 23,0,0,0)
  
  end_date = start_date + timedelta(days=1)
  client , db =  connect_to_db()
  now = datetime.now()
  while end_date < now:
    print("Extract daily info for date: {}".format(start_date))
    simple_date = (start_date.month * 100) +  start_date.day
    days.add(simple_date)
    for tweet in db[cnf.col_tweets].find({"created_at": {"$gte": start_date, "$lt": end_date}},  no_cursor_timeout=True):
      daily_users[simple_date].add(tweet["user"]["id"])
      daily_tweets[simple_date] += 1
      daily_lang[simple_date][tweet["lang"]] += 1
      for hashtag in get_hashtags(tweet):
        daily_hashtags[simple_date][hashtag] += 1
           
    daily_users[simple_date] = len(daily_users[simple_date])
    start_date += timedelta(days=1)
    end_date += timedelta(days=1)
  
  client.close()
   
  f = open("../data/pickle_users.dump","wb")
  obj = dill.dump(daily_users, f)
  f.close()
     
  f = open("../data/pickle_tweets.dump","wb")
  obj = dill.dump(daily_tweets,f)
  f.close()
    
  f = open("../data/pickle_hashtag.dump","wb")
  obj = dill.dump(daily_hashtags, f)
  f.close()
  
  f = open("../data/pickle_lang.dump","wb")
  obj = dill.dump(daily_lang, f)
  f.close()
  
  days = list(days)
  days.sort()
  f_out = open("../data/daily_stats.csv","w+")
  f_out.write("day,daily_users,daily_tweets\n")
  for day in days:
    date = day % 100
    month = calendar.month_name[int((day - date) / 100)][:3]
    f_out.write("{}-{},{},{}\n".format(month, date, daily_users[day], daily_tweets[day] ))
  f_out.close()
  del(daily_users)
  del(daily_tweets)
  

  f_out = open("../data/daily_hashtags.csv", "w+")
  all_hashtags = set()
  all_lang = set()
  for day in days:
    all_hashtags  = all_hashtags.union( set([x  for x in daily_hashtags[day].keys()]))
    all_lang = all_lang.union( set([x for x in daily_lang[day].keys() ]))
  
  all_hashtags = list(all_hashtags)
  all_lang = list(all_lang)
  
  most_popular_hashtags = defaultdict(lambda: 0)
  most_popular_lang = defaultdict(lambda: 0)
  
  
  for day in days:  
    for hs in all_hashtags:
      most_popular_hashtags[hs] += daily_hashtags[day][hs]
    for lang in all_lang: 
      most_popular_lang[lang] += daily_lang[day][lang]
  

  mpl_hashtags = [(hs, most_popular_hashtags[hs]) for hs in most_popular_hashtags]
  mpl_lang = [(lang, most_popular_lang[lang]) for lang in most_popular_lang ]
  mpl_hashtags.sort(key=lambda t:t[1], reverse=True)
  mpl_lang.sort(key=lambda t:t[1], reverse=True)
  
   
  hs_out = open("../data/all_hashtags_data.csv","w+")
  lang_out = open("../data/all_languages_data.csv", "w+")
  hs_out.write("hashtag,number\n")
  lang_out.write("language,number\n")
  
  for hs, cnt in mpl_hashtags:
    hs_out.write("{},{}\n".format(hs, most_popular_hashtags[hs]))
  hs_out.close()
  for lang, cnt in mpl_lang:
    lang_out.write("{},{}\n".format(lang, most_popular_lang[lang]))
  lang_out.close()
  
  hs_out = open("../data/daily_hashtags.csv","w+")
  hs_out.write("date,"+",".join([x[0] for x in mpl_hashtags[:10]])+ "\n")
  for day in days:
    date = day % 100
    month = calendar.month_name[int((day - date) / 100)][:3] 
    line = "{}-{},".format(month, date)
    for i in range(10):
      hs = mpl_hashtags[i][0]
      line+= "{},".format(daily_hashtags[day][hs])
    #line[-1] = "\n"
    hs_out.write(line[:-1] + "\n")
  hs_out.close()

  lang_out = open("../data/daily_lang.csv","w+")
  lang_out.write("date,"+",".join([x[0] for x in mpl_lang[:10]])+ "\n")
  for day in days:
    date = day % 100
    month = calendar.month_name[int((day - date) / 100)][:3]
    line = "{}-{},".format(month, date)
    for i in range(10):
      lang = mpl_lang[i][0]
      line+= "{},".format(daily_lang[day][lang])
    #line[-1] = "\n"
    lang_out.write(line[:-1]+"\n")
  lang_out.close()



def get_active_days():
  global data
  data["activedays"] = (datetime.now() - datetime(2022, 2, 23 )).days


def store_stats():
  global data
  f_out = open("../data/index_stats.txt","w+")
  pairs = [(key, str(data[key])) for key in data]
   
  f_out.write("{}\n{}".format( ",".join([x[0] for x in pairs]), ",".join([x[1] for x in pairs])))
  f_out.close()

if __name__ == "__main__":
   get_db_users_tweets()
   get_suspend()
   get_active_days()
   store_stats()
   get_daily_volume()
