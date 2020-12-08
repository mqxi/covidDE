# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 10:17:35 2020

@author: Maxi
"""
#Verbesserungsvorschläge:
    #Einwohnerzahlen aus einer URL/API implementieren
    #nur senden, wenn die Zahlen sich um mehr als x% entwickelt haben
        #problem: von String in int parsen notwendig (weiß ich zum Stand heute noch nicht wie das geht)

#imports for data requests 
import requests
from bs4 import BeautifulSoup
#imports for email sending (ssl, smtplib) and creating (html, text,..)
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from email.mime.base import MIMEBase
from email import encoders
import smtplib, ssl
#import to delay the process
from time import sleep
#import to draw a diagram as a plot
import pandas as pd
import matplotlib.pyplot as plt


timeNow = datetime.datetime.now() # date and time at the current status
timeNowString= timeNow.strftime("%d.%m.%Y %H:%M:%S") #String formatting in day-month-year hour-minute-second

sender_email = "***" #sender mail adress
receiver_email = "***" #receiver mail adress

file = open("***.txt",'r') # open txt file including the app password 
password = file.readline() #read the password
file.close # closing the file


def graph():
    #copied from https://towardsdatascience.com/visualizing-covid-19-data-beautifully-in-python-in-5-minutes-or-less-affc361b2c6a
# Lädt und wählt folgende Daten aus aus einer csv Datei 
    df = pd.read_csv('https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv', parse_dates=['Date'])
    # Die Keys müssen englisch bleiben, da sonst nicht auf die Werte zugegriffen werden kann 
    countries = ['Canada', 'Germany', 'Switzerland', 'US', 'Australia', 'Kazakhstan']
    # dataframe df wird erstellt und wählt nur die Länder aus, welche vorab angegeben wurden sind 
    df = df[df['Country'].isin(countries)]

# erstellt einen Dataframe, in dem die Gesamtzahl der Fälle in unseren bestätigten Fällen, genesenen Fällen und Todesfälle zusammengefasst werden
    df['Cases'] = df[['Confirmed', 'Recovered', 'Deaths']].sum(axis=1)

# Umformen von Daten (Erstellen einer Pivot-Tabelle) basierend auf Spaltenwerten (Date, Country und Cases).
    df = df.pivot(index='Date', columns='Country', values='Cases')
    # die liste countries beinhaltet alle 
    countries = list(df.columns)
    covid = df.reset_index('Date')
    covid.set_index(['Date'], inplace=True)
    covid.columns = countries

# Calculating Rates per 100,000
#numbers from the 8th of december 2020
    populations = {'Canada': 37885660, 'Germany': 83889154 , 'Switzerland': 8840818 , 'US': 331840730, 'Australia': 26096286, 'Kazakhstan':19171147 }
    percapita = covid.copy()

    for country in list(percapita.columns):
        percapita[country] = percapita[country]/populations[country]*100000

# Generiert Farben und Style
    colors = {'Canada':'#045275', 'Kazakhstan':'#089099', 'Australia':'#7CCBA2', 'Germany':'#FCDE9C', 'US':'#DC3977', 'Switzerland':'#7C1D6F'}
   #style sheet FiveThirtyEight
    plt.style.use('fivethirtyeight')

    percapitaplot = percapita.plot(figsize=(12,8), color=list(colors.values()), linewidth=5, legend=False)
    percapitaplot.grid(color='#d4d4d4')
    percapitaplot.set_xlabel('Datum')
    percapitaplot.set_ylabel('Fälle pro 100.000 Einwohner')

    for country in list(colors.keys()):
        percapitaplot.text(x = percapita.index[-1], y = percapita[country].max(), color = colors[country], s = country, weight = 'bold')
        
    percapitaplot.text(x = percapita.index[1], y = percapita.max().max()+100, s = "Fälle pro 100.000 Einwohner", fontsize = 23, weight = 'bold', alpha = .75)
    percapitaplot.text(x = percapita.index[1], y = percapita.max().max()+500, s = "Für: USA, Kasachstan, Deutschland, Schweiz, Australien und Kanada\n Beinhaltet die Summe aktueller Fälle, genesene Fälle und Todesfälle je Monat seit Februar 2020", fontsize = 16, alpha = .75)
    percapitaplot.text(x = percapita.index[1], y = -1400,s = 'Source: https://github.com/datasets/covid-19/blob/master/data/countries-aggregated.csv', fontsize = 10)
    
    
    plt.savefig('covidgraph.pdf')


def body (confirmed_cases,recovered_cases,deaths,time):

    message = MIMEMultipart() # Multipart braucht man um html, text und ein Anhängsel als Content zusammen zu verwenden
    message["Subject"] = f"SARS-CoV-2 Fälle vom: {timeNowString}" # Titel der E-Mail
    message["From"] = sender_email # Der Message wird die Sender Email zugewiesen
    message["To"] = receiver_email # Der Message wird die Empfänger Email zugewiesen

    email_body = '<html><head></head><body>'
    email_body += '<style type="text/css"></style>' 
    email_body += f'<h2>Bericht der SARS-CoV-2 Fälle in Deutschland am {time}</h2>' 
    #bestätigte Fälle werden zu Email-Body hinzugefügt, in der Farbe blau
    email_body += '<h1 style="color: rgb(0, 0, 204);">' 
    email_body += '<b>bestätigte Fälle</b>: ' 
    email_body += f'{confirmed_cases}</h1>' 
    #genesene Fälle werden zu Email-Body hinzugefügt, in der Farbe grün
    email_body += '<h1 style="color: rgb(0, 204, 0);">' 
    email_body += '<b>Genese Fälle</b>: ' 
    email_body += f'{recovered_cases}</h1>' 
    #Todesfälle werden zu Email-Body hinzugefügt, in der Farbe rot
    email_body += '<h1 style="color: rgb(204, 0, 0);">' 
    email_body += 'Todesfälle </b>: ' 
    email_body += f'{deaths}</h1>' 
    #
    email_body += '<br>Bericht von' 
    email_body += '<br>SARS-CoV-2 Bot</body></html>'
    
    
    # Turn these into html MIMEText objects
    # Add HTML parts to MIMEMultipart message
  
    message.attach(MIMEText(email_body, 'html'))
    #checking if the check function fits
    check()
   
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    # SMTP and Port of your web server Gmail: 587 or 465
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        print(f"Logging in to {sender_email}")
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    
def check():
     #Problem: Wie kann ich eine if Bedingung erstellen, welche vergleicht, ob heute der 1. des Monats ist
   # compare the current datetime and the date of the current day
   # if its the first, it continues
       #dont know if its actually working
    if timeNowString == timeNowString.startswith('1') :
        
        file = "covidgraph.pdf"

        attach_file = open(file, "rb") # open the file in binary mode; decode
        part3 = MIMEBase("application", "octate-stream") #some MIMEBase needed informations for attachments are saved in part3
        part3.set_payload((attach_file).read()) # read the file in binary mode
        encoders.encode_base64(part3) # encode the file into ASCII characters
        part3.add_header('Content-Disposition', 'attachment', filename=file) # add header to create the pdf symbol and an visable attachment (in Mail)
        # Add attachment part to MIMEMultipart objects
        body().message.attach(part3) # add the part to the message 
    else:
        print('No Attachment today')
            
#url of the covid dates
url = "https://www.worldometers.info/coronavirus/country/germany/"
#req object saved with the saved url
req = requests.get(url)
#beautiful soup object is created due to the req object to parse the dates into html
bsObj = BeautifulSoup(req.text, "html.parser")
data = bsObj.find_all("div",class_ = "maincounter-number")
#from the url, the data which we searching for gets implemented in variables
numTotalCase = data[0].text.strip().replace(',', '')
numDeaths = data[1].text.strip().replace(',', '')
numRecovered = data[2].text.strip().replace(',', '')


executer = True
#loop to start the whole process
while executer == True:
    # condition to receive an email:
        #Problem and idea are described in line 9 to 10
         #implement an counter
    c=str(0)
    if numRecovered > numDeaths :
       
        #execute the needed functions
        print('create Text message')
        body(numTotalCase,numRecovered,numDeaths,timeNowString)
        print('checks condition...')
        # confirmation
        print('E-Mail sent! The ' + c +' time')
        c+=str(1)

        #execute the process again, one day later 1440 seconds
        sleep(1440)
        #protect my mail client from receiving this mail too often; decision taken based on errors while testing
        if c == 3:
            executer = False
            