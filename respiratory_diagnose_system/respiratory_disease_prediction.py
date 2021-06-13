from flask import Flask ,render_template,request,jsonify,session
from flask import Flask,abort,render_template,request,redirect,url_for
from werkzeug import secure_filename
import os
import sqlite3 as sql
import base64
import pandas as pd
from sklearn.preprocessing import LabelEncoder
#from flask_bootstrap import Bootstrap
import numpy as np
from sklearn.utils import shuffle


app = Flask(__name__)

app.secret_key = 'any random string'

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

   
def validate(username,password):
    con = sql.connect('static/chat.db')
    completion = False
    with con:
        cur = con.cursor()
        cur.execute('SELECT * FROM persons')
        rows = cur.fetchall()
        for row in rows:
            dbuser = row[1]
            dbpass = row[2]
            if dbuser == username:
                completion = (dbpass == password)
    return completion


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        completion = validate(username,password)
        if completion == False:
            error = 'invalid Credentials. please try again.'
        else:
            session['username'] = request.form['username']
            return render_template('index111.html')
    return render_template('index111.html', error=error)


@app.route('/view', methods=['GET', 'POST'])
def view():
    
    return render_template('index111.html')

    
@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            username = request.form['username']
            password = request.form['password']
            with sql.connect("static/chat.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO persons(name,username,password) VALUES (?,?,?)",(name,username,password))
                con.commit()
                msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"
        finally:
            return render_template("index.html",msg = msg)
            con.close()
    return render_template('register.html')


@app.route('/list')
def list():
   con = sql.connect("static/chat.db")
   con.row_factory = sql.Row
   
   cur = con.cursor()
   cur.execute("select * from persons")
   
   rows = cur.fetchall();
   return render_template("list.html",rows = rows)

@app.route('/crop_predict',methods=['GET','POST'])
def crop():

    dataset = pd.read_csv('dataset/preprocess_dataset.csv')
    
    X = dataset.iloc[:,[1,2,3,5,6]].values
    y = dataset.iloc[:,4].values

    # encoding categorical data e.g. gender as a dummy variable
    from sklearn.preprocessing import LabelEncoder
    labelencoder_X = LabelEncoder()
    X[:,1] = labelencoder_X.fit_transform(X[:,1])

    # encoding categorical data e.g. disease outcome as a dummy variable
    y,class_names = pd.factorize(y)

    # Splitting the dataset into the Training set and Test set
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25, random_state = 42)

    # Fitting Classifier to the Training Set
    from sklearn.tree import DecisionTreeClassifier
    classifier = DecisionTreeClassifier(criterion='entropy',max_depth=3, random_state=42)
    classifier.fit(X_train, y_train)
    prediction2=[]
    
    if request.method == 'POST':
        A = request.form['Age']
        N = request.form['Gender']
        P = request.form['BMI']
        K = request.form['crackles']
        ph = request.form['wheezes']
        

        print(A,N,P,K,ph)
        
        columns = ['A','N','P','K','ph']
        values = np.array([A,N,P,K,ph])
        pred = pd.DataFrame(values.reshape(-1, len(values)),columns=columns)

        prediction = classifier.predict(pred)

        if prediction==5:
            print('Bronchiolitis')
            prediction1='Bronchiolitis'
        if prediction==4:
            print('Pneumonia')
            prediction1='Pneumonia'
        if prediction==3:
            print('Bronchiectasis')
            prediction1='Bronchiectasis'
        if prediction==2:
            print('COPD')
            prediction1='COPD'
        if prediction==1:
            print('Healthy')
            prediction1='Healthy'
        if prediction==0:
            print('URTI')
            prediction1='URTI'
            
     
        prediction2.append(prediction1)
    return render_template('crop.html',predict=prediction2,display=True)




@app.route('/crop_pre',methods=['GET','POST'])
def crop1():
    dataset = pd.read_csv('dataset/preprocess_dataset.csv')
    
    X = dataset.iloc[:,[1,2,3,5,6]].values
    y = dataset.iloc[:,4].values

    # encoding categorical data e.g. gender as a dummy variable
    from sklearn.preprocessing import LabelEncoder
    labelencoder_X = LabelEncoder()
    X[:,1] = labelencoder_X.fit_transform(X[:,1])

    # encoding categorical data e.g. disease outcome as a dummy variable
    y,class_names = pd.factorize(y)

    # Splitting the dataset into the Training set and Test set
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25, random_state = 42)

    # Fitting Classifier to the Training Set
    from sklearn.tree import DecisionTreeClassifier
    classifier = DecisionTreeClassifier(criterion='entropy',max_depth=3, random_state=42)
    classifier.fit(X_train, y_train)
    prediction1=[]
    
    prediction2=[]
    if request.method == 'POST':
        A = request.form['Age']
        N = request.form['Gender']
        P = request.form['BMI']
        print(A,N,P)
        file1=request.form['file']

        import glob
        path = r'respiratory_sound_database/Respiratory_Sound_Database/audio_and_txt_files'
        file = r'respiratory_sound_database/Respiratory_Sound_Database/audio_and_txt_files/'+file1+'.txt'
        all_files = glob.glob(file)
        def AnnotationData(filename, path):
            words = filename[len(path):-4].split('_')
            recording_info = pd.DataFrame(data = [words], columns = ['Patient number', 'Recording index', 'Chest location','Acquisition mode','Recording equipment'])
            recording_annotations = pd.read_csv(filename, names = ['t_start', 't_end', 'Crackles', 'Wheezes'], delim_whitespace=True)
            return (recording_info, recording_annotations)
        infoList=[]
        
        
        prediction2=[]
        for filename in all_files:
            (info, annotation) = AnnotationData(filename, path)
    
            crackles = annotation['Crackles'].sum()
            wheezes = annotation['Wheezes'].sum()
            # Summed number of crackles / wheezes are normalized by the duration of the recording
            duration = annotation.iloc[-1, 1] - annotation.iloc[0, 0]
            info['Crackles'] = crackles/duration # crackles per second
            info['Wheezes'] = wheezes/duration # wheezes per second
            infoList.append(info)
            K=float(info['Crackles'])
            ph=float(info['Wheezes'])
            columns = ['A','N','P','K','ph']
            
            print([A,N,P,K,ph])
            values = np.array([A,N,P,K,ph])
            pred = pd.DataFrame(values.reshape(-1, len(values)),columns=columns)

            #prediction = classifier.predict(pred)
            prediction = classifier.predict(pred)
            print(prediction)
            prediction2=[]
            if prediction==5:
                print('Healthy')
                prediction1='Healthy'
            if prediction==4:
                print('Pneumonia')
                prediction1='Pneumonia'
            if prediction==3:
                print('Bronchiectasis')
                prediction1='Bronchiectasis'
            if prediction==2:
                print('COPD')
                prediction1='COPD'
            if prediction==1:
                print('Bronchiolitis')
                prediction1='Bronchiolitis'
            if prediction==0:
                print('URTI')
                prediction1='URTI'
            
     
        prediction2.append(prediction1)
    return render_template('crop1.html',predict=prediction2,display=True)


	


	

    
    
if __name__ == '__main__':
   app.run(debug = True )
