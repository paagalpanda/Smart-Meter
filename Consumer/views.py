from django.shortcuts import render,redirect
from django.http import request,HttpResponse,JsonResponse
from .models import *
import requests
import smtplib


import json
import pandas as pd
from sklearn import svm
import numpy as np
#from sklearn import cross_validation
from sklearn import preprocessing as pre
from datetime import datetime
from django.contrib.auth import login,logout,authenticate
import os

#import pymysql

# Create your views here.
def base_layout(request):
	template='Consumer/base.html'
	return render(request,template)
    
def send_otp(request):
    if request.method == 'POST':
        pnno = request.POST.get('cno')
        #if ConsumerDetails.objects.filter(consumer_no = cno):
         #   return HttpResponse("success")
        #else:
         #   return HttpResponse(cno)
        #user_phone = request.POST['phone_number']
        url = "http://2factor.in/API/V1/85e7693b-90d2-11e9-ade6-0200cd936042/SMS/"+pnno+"/AUTOGEN"
        response = requests.get(url)
        data = response.json()
        request.session['otp_session_data'] = data['Details']
        # otp_session_data is stored in session.
        #response_data = {'Message':'Success'}
        return redirect(otp_verification)
    return render(request,'Consumer/check.html')

def otp_verification(request):
	response_data = {}
	if request.method == "POST":
		user_otp = request.POST['otp']
		url = "http://2factor.in/API/V1/293832-67745-11e5-88de-5600000c6b13/SMS/VERIFY/" + request.session['otp_session_data'] + "/" + user_otp + ""
        # otp_session_data is fetched from session.
		response = requests.request("GET", url)		
		data = response.json()
		if data['Status'] == "Success":
			return redirect('signup')
		else:
			response_data = {'Message':'Failed'}
			logout(request)
	return JsonResponse(response_data)

def ulogin(request):
    if request.method == 'POST':
        uname = request.POST.get("uname")
        pswd = request.POST.get("pswd")
        user = authenticate(request,username=uname,password=pswd)
        if user is not None:
            login(request,user)
            return redirect('usage')
        else:
            return HttpResponse("user not valid")
    return render(request,'Consumer/login.html')

def usage(request):
    #s = os.path.dirname(os.path.abspath(__file__))
    #return render(request,'Consumer/usage.html',{'s':s})
    #f = open("Consumer\\data\\final.csv",'rb')
    data = pd.read_csv("Consumer\\data\\final.csv",parse_dates=['timestamp'],index_col='timestamp')
    final = data.groupby(data.index.month)
    m_total = {}
    d_total = {}
    h_total = {}

    # monthly consumption
    for i,d in final:
        m_total.update({str(i):str(round(d.USAGE.sum(),2))})

    # daily consumption
    for i,d in final:
        for day in set(d.index.day):
            d_total.update({str(day):str(d[d.index.day==day]['USAGE'].sum())})
        break
    
    # hourly consumption
    for i,d in final:
        for day in set(d.index.day):
            #l=[]
            #print(i,day)
            for hr in set(d.index.hour):
                h_total.update({str(hr):str(d[(d.index.hour==hr) & (d.index.day==day)].USAGE.sum())})
            break
        break 
    

    # prediction of power consumption for the month
    old = pd.read_csv("Consumer\\data\\final.csv",parse_dates=['timestamp'],index_col='timestamp')
    train_start = '1-march-2019'
    train_end = '25-march-2019'
    test_start = '26-march-2019'
    test_end = '30-april-2019'

    X_train_df = old[train_start:train_end]
    del X_train_df['USAGE']
    del X_train_df['timestamp_end']
    del X_train_df['wspdm']

    y_train_df = old['USAGE'][train_start:train_end]

    X_test_df = old[test_start:test_end]
    del X_test_df['USAGE']
    del X_test_df['timestamp_end']
    del X_test_df['wspdm']

    y_test_df = old['USAGE'][test_start:test_end]

    # Numpy arrays for sklearn
    X_train = np.array(X_train_df)
    X_test = np.array(X_test_df)
    y_train = np.array(y_train_df)
    y_test = np.array(y_test_df)

    scaler = pre.StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    SVR_model = svm.SVR(kernel='rbf',C=100,gamma=.001).fit(X_train_scaled,y_train)
    #print('Testing R^2 =', round(SVR_model.score(X_test_scaled,y_test),3))

    # Use SVR model to calculate predicted next-hour usage
    predict_y_array = SVR_model.predict(X_test_scaled)
    # Put it in a Pandas dataframe for ease of use
    predict_y = pd.DataFrame(predict_y_array,columns=['USAGE'])
    predict_y.index = X_test_df.index

    predict = list(zip(predict_y.index,predict_y_array))    

    context = {
        'month' : m_total,
        'day':d_total,
        'hr':h_total,
        'predict':predict
    }
    return render(request,'Consumer/usage.html',context=context)

def payment(request):
    if request.method == 'POST':
        return redirect('bill',request.POST.get('amount'))
    c = Payment.objects.all()
    result = []
    for row in c:
        result.append(row)
    return render(request,'Consumer/pay.html',context={'history':result})

def bill(request):
    #amount = request.POST['amount']
    
    
    data = pd.read_csv('Consumer\\data\\final.csv',parse_dates=['timestamp'],index_col='timestamp')
    final = data.groupby(data.index.month)
    units = 0
    amount = 0
    for i,d in final:
            for month in set(d.index.month):
                #l=[]
                #print(i,day)
                #print(month)
                if month in range(3,10):
                    #print(d.USAGE.sum())
                    punits = 0
                    npunits =0
                    amount1 = 0
                    amount2 = 0
                
                    for hr in set(d.index.hour):
                        
                        
                        if hr in range(14,19):
                            
                            punits +=  d[(d.index.month == month) & (d.index.hour == hr)].USAGE.sum()
                            
                        else:
                            npunits +=d[(d.index.month==month)& (d.index.hour==hr)].USAGE.sum()
                            
                    if npunits <= 50 :
                        amount1 = npunits * 3.85
                    elif npunits <= 150:
                        amount1 = 182.5 + (npunits-50) * 6.10
                    elif npunits <= 300:
                        amount1 = 182.5 + 610 + (npunits-150) * 6.40
                    elif npunits <= 500:
                        amount1 = 182.5 + 610 + 960 + (npunits-300) * 6.70
                    else:
                        amount1 = 182.5 + 610 + 960 + 1340 + (npunits-500) * 7.15
                    
                        
                    if punits <= 50 :
                        amount2 = punits * 4.85
                    elif punits <= 150:
                        amount2 = 242.5 + (punits-50) * 7.10
                    elif punits <= 300:
                        amount2 = 242.5 + 710 + (punits-150) * 7.40
                    elif punits <= 500:
                        amount2 = 242.5 + 710 + 1110 + (punits-300) * 7.70
                    else:
                        amount2 = 242.5 + 710 + 1110 + 1540 + (punits-500) * 8.15
                    amount = amount1+amount2
            
                    print(amount)
    return JsonResponse({'punits':punits,'npunits':npunits,'amount':amount})


def email(request):
    if request.method=='POST':
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        #Next, log in to the server
        server.login("aditirathore4nov@gmail.com", "aditirathore")

        #Send the mail
        msg = "Hello Pinguu!" # The /n separates the message from the headers
        server.sendmail("aditirathore4nov@gmail.com", "8426813488@vtext.com", msg)
        return HttpResponse("done")
    return render(request,'Consumer/email.html')
