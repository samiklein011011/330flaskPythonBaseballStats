from flask import *
import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from plotnine import *
from plotnine.data import *
import re
import os, sys
from dfply import *
import seaborn as sns; sns.set()
from werkzeug import secure_filename


UPLOAD_FOLDER = '/home/kdorian/creative/app/static'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my secret string'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def hello():
    return(render_template('welcome.html'))

@app.route('/viz', methods=['GET', 'POST'])
def viz():
     if request.method == 'POST':
         f = request.files['file']
         f.save(secure_filename('pitch.csv'))
         return(render_template("viz.html", name = f.filename))
     else:
         return(render_template("viz.html"))

@app.route('/velo')
def velo():
    pitches = pd.read_csv('pitch.csv')
    plot = ggplot(pitches, aes('Pitch_Number', 'Velo', colour='Pitch'))+\
      geom_line()+\
      geom_point(size = 1)+\
      facet_wrap('~Date', ncol=2)
    plot.save("/home/kdorian/creative/app/static/velo.jpg")
    return(render_template("velo.html"))

@app.route('/zone')
def zone():
    pitches =  pd.read_csv('pitch.csv')
    pitch = pitches >> select(X.Hor,X.Vert) >> group_by(X.Hor, X.Vert) >> summarize(tot = n(X.Hor)) >> spread(X.Hor, X.tot)
    pitch = pitch.set_index('Vert')
    zoneVis = sns.heatmap(pitch)
    fig = zoneVis.get_figure()
    fig.savefig('/home/kdorian/creative/app/static/zone.jpg')
    return(render_template("zone.html"))



@app.route('/dashboard', methods = ['POST', 'GET'])
def dash():
   if request.method == 'POST':
      code = request.form['TeamCode']
      session['code'] = code
      url='https://stats.ncaa.org/game_upload/team_codes'
      page = requests.get(url)
      html = page.content
      soup = BeautifulSoup(html, 'lxml')
      table = soup.find('table')
      list_of_rows = []
      for row in table.findAll('tr'):
          list_of_cells = []
          for cell in row.findAll('td'):
              text = cell.text.replace("\n", '')
              text = cell.text.replace('nbsp&', '')
              list_of_cells.append(text)
          list_of_rows.append(list_of_cells)

      names = ['Team']
      data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
      array = pd.DataFrame(data=data,columns=names)
      array = array.replace('\n\n\n',0)
      for i in range(1,len(array)):
        if(array['Team'][i][0] == code):
          name = array['Team'][i][1]
          session['name'] = name
      return(render_template("dashboard.html",result = code, team = name))
   else:
      return(render_template("dashboard.html", result = session['code'], team = session['name']))


@app.route('/hitting', methods = ['POST', 'GET'])
def hitting():
    url='https://stats.ncaa.org/team/' + session['code'] + '/stats/12973'
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('tbody')
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace('\n', '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)

    names = ['Number', 'Player','Year','Position','GP','GS','G','BA','OBP','SLG','R','AB','H','2B','3B','TB','HR','RBI','BB','HBP','SF','SB','K','DP','CS','PO','SB','RBI2Out']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array['G'][2] = 'ha'
    return(render_template('table.html', output = array.to_html()))

@app.route('/pitching', methods = ['POST', 'GET'])
def pitching():
    url='https://stats.ncaa.org/team/'+session['code']+'/stats?id=12973&year_stat_category_id=11954'
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('tbody')
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace('\n', '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)

    names = ['Number', 'Player','Year','Position','GP','GS','G','APP','pGS','ERA','IP','CG','H','R','ER','BB','SO','SHO','BF','pOAB','2bA','3bA','Bk','HrA','WP','HB','IBB','InhRun','InhRS','SBA','SFA','Pitches','GO','FO','W','L','SV','KL']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array['pGS'] = array['pGS'].replace('\n','')
    array = array.replace('\n\n\n','')
    return(render_template('table.html', output = array.to_html()))

@app.route('/fielding', methods = ['POST', 'GET'])
def fielding():
    url='https://stats.ncaa.org/team/'+session['code']+'/stats?id=12973&year_stat_category_id=11955'
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('tbody')
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace('\n', '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)

    names = ['Number', 'Player','Year','Position','GP','GS','G','PO','TC','A','E','FLD%','CI','PB','SBA','CSB','IDP','TP']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array = array.replace('\n\n\n',0)
    return(render_template('table.html', output = array.to_html()))

@app.route('/roster', methods = ['POST', 'GET'])
def roster():
    url='https://stats.ncaa.org/team/'+session['code']+'/roster/12973'
    #Create a handle, page, to handle the contents of the website
    page = requests.get(url)
    #Store the contents of the website under doc
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('tbody')
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace("\n", '')
            text = cell.text.replace('nbsp&', '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)

    names = ['Number', 'Player','Position','Year','Games Played','Games Started']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array = array.replace('\n\n\n',0)
    return(render_template('table.html', output = array.to_html()))

@app.route('/schedule', methods = ['POST', 'GET'])
def schedule():
     beg = 'https://stats.ncaa.org'
     start = 'https://stats.ncaa.org/team/'+ session['code'] + '/roster/12973'
     pageStart = requests.get(start)
     html1 = pageStart.content
     soup1 = BeautifulSoup(html1, 'lxml')
     links = []
     for link in soup1.findAll('a', attrs={'href': re.compile("/teams")}):
       links.append(link.get('href'))
     url = beg + links[2]
     #Create a handle, page, to handle the contents of the website
     page = requests.get(url)
     #Store the contents of the website under doc
     html = page.content
     soup = BeautifulSoup(html, 'lxml')
     table = soup.find('table', {'class': 'mytable', 'width':'100%'})
     list_of_rows = []
     for row in table.findAll('tr'):
         list_of_cells = []
         for cell in row.findAll('td', {'class': 'smtext'}):
             text = cell.text.replace("\n", '')
             text = cell.text.replace('nbsp&', '')
             list_of_cells.append(text)
         list_of_rows.append(list_of_cells)

     names = ['all']
     data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
     array = pd.DataFrame(data=data,columns=names)
     array = array.iloc[2:]
     array = array.replace('\n\n\n',0)
     array.index = range(0,len(array['all']))
     dates = []
     opponents = []
     results = []

     for i in range(0, len(array['all'])):
       dates.append(array['all'][i][0])
       opponents.append(array['all'][i][1])
       opponents[i] = opponents[i][1:]
       opponents[i] = opponents[i][:-1]
       results.append(array['all'][i][2])
       results[i] = results[i][1:]
       results[i] = results[i][:-1]

     Dates = pd.Series(dates)
     Opponents = pd.Series(opponents)
     Results = pd.Series(results)

     schedule = pd.concat([Dates, Opponents, Results], axis = 1)
     schedule.columns = ['Date', 'Opponent','Result']
     schedule.replace('\n','')
     return(render_template('table.html', output = schedule.to_html()))


@app.route('/SOS', methods = ['POST', 'GET'])
def SOS():
    url='https://www.d3baseball.com/seasons/2018/schedule?tmpl=sos-template'
    #Create a handle, page, to handle the contents of the website
    page = requests.get(url)
    #Store the contents of the website under doc
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table', {'border': '0', 'width':'600px'})
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace("\n", '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)
    names = ['Team','Regional Record', 'Regional Win%','OWP (Rank)','OOWP', 'NCAA']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array = array.iloc[1:]
    return(render_template('table1.html', output = array.to_html()))



@app.route('/top25', methods = ['POST', 'GET'])
def top25():
    url='https://www.d3baseball.com/top25/2018/2018Top25-week-final'
    #Create a handle, page, to handle the contents of the website
    page = requests.get(url)
    #Store the contents of the website under doc
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('tbody')
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace("\n", '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)
    names = ['#','School (1st Votes)', 'Rec','Pts','Prev']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array = array.replace('\n\n\n','')
    array = array.iloc[1:]
    array.index = range(1, len(array)+1)
    array.drop("#",axis=1,inplace=True)
    return(render_template('table1.html', output = array.to_html()))


@app.route('/plays', methods = ['POST', 'GET'])
def getPlays():
  start = 'https://stats.ncaa.org/team/'+ session['code'] + '/roster/12973'
  page1 = requests.get(start)
  html1 = page1.content
  soup1 = BeautifulSoup(html1, 'lxml')
  direct = []
  for link in soup1.findAll('a', attrs={'href': re.compile("^/teams")}):
    direct.append(link.get('href'))
  url = "https://stats.ncaa.org" + direct[2]
  page = requests.get(url)
  html = page.content
  soup = BeautifulSoup(html, 'lxml')
  links = []
  for link in soup.findAll('a', attrs={'href': re.compile("^/game")}):
    links.append(link.get('href'))
  links = ['https://stats.ncaa.org/' + s[1:5] + '/play_by_play' + s[11:19] for s in links]
  url = links[0]
  page = requests.get(url)
  html = page.content
  soup = BeautifulSoup(html, 'lxml')
  tables = soup.findAll('table', {'class': 'mytable', 'align': 'center', 'width':'100px'})
  list_of_cells = []
  for cell in soup.findAll('td', {'class': 'smtext'}):
     text = cell.text.replace("\n", '')
     list_of_cells.append(text)
  list_of_cells[:] = [item for item in list_of_cells if item != '']
  names = ['Events']
  data = np.array(list_of_cells).reshape(len(list_of_cells),len(names))
  Frame = pd.DataFrame(data=data,columns=names)
  for i in range(1, len(links)):
    url = links[i]
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.findAll('table', {'class': 'mytable', 'align': 'center', 'width':'100px'})
    list_of_cells = []
    for cell in soup.findAll('td', {'class': 'smtext'}):
       text = cell.text.replace("\n", '')
       list_of_cells.append(text.strip('\n'))
    list_of_cells[:] = [item for item in list_of_cells if item != '']
    names = ['Events']
    data = np.array(list_of_cells).reshape(len(list_of_cells),len(names))
    array = pd.DataFrame(data=data,columns=names)
    Frame = Frame.append(pd.DataFrame(data = array), ignore_index=True)
  return(render_template('table.html', output = Frame.to_html()))

@app.route('/teamCodes', methods = ['POST', 'GET'])
def teamCodes():
    return(render_template('teamCodes.html', code = session['code']))

@app.route('/answer', methods = ['POST', 'GET'])
def answer():
    if request.method == 'POST':
       name = request.form['TeamName']
    url='https://stats.ncaa.org/game_upload/team_codes'
    page = requests.get(url)
    html = page.content
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table')
    list_of_rows = []
    for row in table.findAll('tr'):
        list_of_cells = []
        for cell in row.findAll('td'):
            text = cell.text.replace("\n", '')
            text = cell.text.replace('nbsp&', '')
            list_of_cells.append(text)
        list_of_rows.append(list_of_cells)

    names = ['Team']
    data = np.array(list_of_rows).reshape(len(list_of_rows),len(names))
    array = pd.DataFrame(data=data,columns=names)
    array = array.replace('\n\n\n',0)
    code = '?-Check Spelling'
    for i in range(1,len(array)):
      if(array['Team'][i][1] == name):
        code = array['Team'][i][0]
    return(render_template("answer.html",name = name, code = code))

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')
