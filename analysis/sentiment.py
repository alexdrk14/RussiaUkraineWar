import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
import pandas as pd
from collections import defaultdict
from matplotlib.legend_handler import HandlerBase
import matplotlib
import matplotlib.lines
from matplotlib.transforms import Bbox, TransformedBbox
from matplotlib.legend_handler import HandlerBase
from matplotlib.image import BboxImage
import config as cnf
import calendar

PATH_SENT = cnf.sentiment_files
SENT_PREFIX = cnf.sentiment_prefix



def compute_sentiment():
  """Get list of files with sentiment"""
  onlyfiles = [join(PATH_SENT ,f) for f in listdir(PATH_SENT) if isfile(join(PATH_SENT, f)) and f.endswith(".csv") and SENT_PREFIX in f  ]
  files_by_date = []
  for filename in onlyfiles:
    
    date = filename.split(SENT_PREFIX)[1].split("_")[0].split("-")
    date = int(date[0]) * 100 + int(date[1])
    files_by_date.append((date, filename))

  sentiment = defaultdict(lambda: [])
  files_by_date.sort(key=lambda t:t[0])
  dates = []
  for date, filename in files_by_date:
    df = pd.read_csv(filename, sep="\t")
    """Create date label in format like: Feb-23"""
    day = date % 100
    month = calendar.month_name[int((date - day)/100)][:3]

    dates.append( "{}-{}".format(month, day) )

    sentiment["positive_for_ukraine"].append(df["positive_for_ukraine"][0])
    sentiment["positive_for_zelensky"].append(df["positive_for_zelensky"][0])
    sentiment["positive_for_russia"].append(df["positive_for_russia"][0])
    sentiment["positive_for_putin"].append(df["positive_for_putin"][0])
    sentiment["positive_for_war"].append(df["positive_for_war"][0])
    sentiment["negative_for_ukraine"].append(-1.0*df["negative_for_ukraine"][0])
    sentiment["negative_for_zelensky"].append(-1.0*df["negative_for_zelensky"][0])
    sentiment["negative_for_russia"].append(-1.0*df["negative_for_russia"][0])
    sentiment["negative_for_putin"].append(-1.0*df["negative_for_putin"][0])
    sentiment["negative_for_war"].append(-1.0*df["negative_for_war"][0])


  f_out = open("../data/daily_sentiment.csv","w+")
  f_out.write("date,ukrain_pos,ukrain_neg,russia_pos,russia_neg,zelensky_pos,zelensky_neg,putin_pos,putin_neg\n")
  for i in range(len(dates)):
    f_out.write("{},{},{},{},{},{},{},{},{}\n".format(dates[i], sentiment["positive_for_ukraine"][i], sentiment["negative_for_ukraine"][i], 
                                         sentiment["positive_for_russia"][i],  sentiment["negative_for_russia"][i],
                                         sentiment["positive_for_zelensky"][i],sentiment["negative_for_zelensky"][i],
                                         sentiment["positive_for_putin"][i],   sentiment["negative_for_putin"][i]))
  f_out.close()


if __name__ == "__main__":
  compute_sentiment()


