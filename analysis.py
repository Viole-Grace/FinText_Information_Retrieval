import re
import json
from collections import defaultdict
from nltk import ngrams
from nltk.tokenize import word_tokenize
from collections import OrderedDict

DATAPOINTS = ["delivery_currency", "delivery_amount", "delivery_rounding","return_currency", "return_amount", "return_rounding"]

def read_json(filename):

	with open(filename,"r") as f_p:
		list_isda_data = json.load(f_p)
	print "LIST DATA : unicode characters detected. Manually removing them."
	print "Cleaned JSON data..."
	cleaned_data = json_load_byteified(open(filename));
	print "Sending cleaned data for information extraction"
	return cleaned_data

def json_load_byteified(file_handle): #if you want to check with filenames
	return convbytes(json.load(file_handle, object_hook=convbytes),ignore_dicts=True)

def json_loads_byteified(json_text): #if you want to check with text data without filenames
	return convbytes(json.loads(json_text, object_hook=convbytes),ignore_dicts=True)

def convbytes(data, ignore_dicts=False):
	if isinstance(data,unicode):
		return data.encode('utf-8')
	if isinstance(data, list):
		return [ convbytes(item, ignore_dicts=True) for item in data ]
	if isinstance(data, dict) and not ignore_dicts:
		return { convbytes(key, ignore_dicts=True): convbytes(value, ignore_dicts=True) for key,value in data.iteritems() }
	return data

def extract(data):
	#we have the cleaned data from read_json()
	#we need to get the data we need for stopwords, i.e, the text needs to be processed.

	#SOLUTION and Explanation : 
	#remove stopwords first and then use regex.compile and pattern.check to find currency, rounding type and amount.	
	#amount appears right after currency, so extract format should be `currency`:`amount`. use regex.compile for this.
	#if currency regex matches more than once, then compare return_curr with delivery_curr
	#if "rounding" occurs anywhere, note the type. if type is not mentioned, take nearest as default.
	#if "rounding" occurs multiple times, take the first and last occurrance of rounding, one will be deliver, the other will be return
	#match amount regex if it appears multiple times. first occurrance is delivery, next occurrance is return.

	#start by finding stopwords. Take the stopwords file. Note: not using the stopwords from nltk.corpus since it has a few common words missing.
	stopwords,finwords=[],[]
	with open("stopwords.txt","r+") as stop:
		for line in stop:
			for word in line.split():
				stopwords.append(word)
	
	#extract "text" from the data object parsed from read_json().
	#remove stopwords from "text" and tokenize words, form bi-grams for regex matching at currency and rounding.

	text_data=[datum['text']for datum in data][0].lower()
	print "TEXT DATA : \n",text_data
	word_tokens=word_tokenize(text_data)
	filtered_sentence=[w for w in word_tokens if not w in stopwords]
	print "\nGetting bi-grams"
	#bi-grams are a text input mechanism, so we will do a copy from list -> text as well to send to the param.

	st_text=""
	info_list=[]
	for item in filtered_sentence:
		st_text=st_text+" "+item
	info_list = get_bigrams(st_text)
	#bi-grams have been formed, returned. Now a simple return and regex check for the phrases we are looking for :

	curr_type_and_amount, rounding_type, it, it1 = [],[],0,0
	for item in info_list:
		del_curr = re.match("[a-z]{3}_[0-9]",item)
		if del_curr:
			curr_type_and_amount.insert(it+1,item)
		if item == "rounded_up" or item == "rounded_down" or item == "rounded_nearest":
			print item
			rounding_type.insert(it1+1,item)
	#currency type and amount has been found. Let us move to delivery type and amount.
	#if currency type and amount is found more than once, the latter type and amount is return, not delivery
	#if rounded type is found more than once, former is delivery, latter is return
	#if found only once, that means return param = del param.

	#print "CURR TYPE AND AMOUNT : \n",curr_type_and_amount
	#print "ROUNDING TYPE: \n",rounding_type
	#search for number of items and decide what item could be where.

	# INTUITION p1:

	#1st item in list1 would be currency type + amount, 2nd list would be rounding type.
	#if there is a 2nd item in list1, it could be return curr/amount.
	#if there is a 2nd item in list2, it could be return rounding type.

	# INTUITION p2:

	#if there is only one item in both lists, return param = delivery param.
	#if there is only one item in list1, and no items in list2, return param = delivery param AND rounding type =  nearest.
	datap=OrderedDict()
	""""""
	datap["delivery_currency"]=""
	datap["delivery_amount"]=""
	datap["delivery_rounding"]=""
	datap["return_currency"]=""
	datap["return_amount"]=""
	datap["return_rounding"]=""

	if len(rounding_type) == 0:
		datap["delivery_rounding"]="nearest"
		datap["return_rounding"]="nearest"
	else :
		datap["delivery_rounding"]=rounding_type[0][8:]
		datap["return_rounding"]=rounding_type[len(rounding_type)-1][8:]

	datap["delivery_currency"]=curr_type_and_amount[0][0:3].upper()
	datap["delivery_amount"]=curr_type_and_amount[0][4:]

	datap["return_currency"]=curr_type_and_amount[len(curr_type_and_amount)-1][0:3].upper()
	datap["return_amount"]=curr_type_and_amount[len(curr_type_and_amount)-1][4:]

	for key,value in datap.items():
		print key,": ",value

	predicted_output=[]
	for datum in data:
		predicted_output.append(datap)

	return predicted_output

def get_bigrams(text):
	bi_grams=ngrams(text.split(),2) #set number type of n-grams. We want bi-grams, hence we are using '2' as our param.
	l=[]
	for grams in bi_grams:
		l.append('_'.join(map(str,grams)))
	#f1= ' '.join(l) = string output for the bi-grams. We want a list output to re.match() for delivery amount, etc.
	#print l
	return l

def evaluate(input_data, predicted_output):
    """The function computes the accuracy for each of the datapoints
    that are part of the information extraction problem.

    Args:
        input_data (list): The input is a list of dictionary values from the isda json file
        predicted_output (list): This is a list which the information extraction algorithm should extract from the text

    Returns:
        dict: The function returns a dictionary which contains the number of exact between the input and the output
    """

    result = defaultdict(lambda: 0)
    for i, input_instance in enumerate(input_data):
        for key in DATAPOINTS:
            if input_instance[key] == predicted_output[i][key]:
                result[key] += 1

    # compute the accuracy for each datapoint
    print "\nACCURACY : \n"
    for key in DATAPOINTS:
        print(key, 1.0 * result[key] / len(input_data))

    return result
fname=raw_input("Enter filename you want to use for the IR module : ")
data=read_json(fname)
pred_out=extract(data)
result=evaluate(data,pred_out)