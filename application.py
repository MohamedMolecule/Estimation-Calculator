from flask import Flask, session, redirect, request, render_template
import sqlite3

app = Flask(__name__)
app.secret_key = '\xbf7r\r\xe9\xdf\x14\xf1\xc3n\x17\x8e'


@app.route("/", methods=["POST", "GET"])
def login():
    connection = sqlite3.connect("data.db")
    crsr = connection.cursor() 
    if request.method == "POST":
        if request.form['submitbutton'] == "register":
            return redirect("/register")
        username = request.form.get("username").lower()
        password = request.form.get("password")
        if len(username) > 255 or len(password) > 255:
            return render_template("login.html", alert="Username or password has more than 255 digits")
        if username == "":
            return render_template("login.html", alert="Enter a valid username")
        if password == "":
            return render_template("login.html", alert="Enter a valid password")
        crsr.execute("SELECT username FROM users WHERE username=:username;", {"username": username})
        sqldata = crsr.fetchall()
        if len(sqldata) == 0:
            return render_template("login.html", alert="Username doesn't exist")
        crsr.execute("SELECT password FROM users WHERE username=:username;", {"username": username})
        sqldata = crsr.fetchall()
        passwordsql = sqldata[0][0]
        if str(password) != str(passwordsql):
            return render_template("login.html", alert="Incorrect password")
        crsr.execute("SELECT id FROM users WHERE username=:username;", {"username": username})
        sqldata = crsr.fetchall()
        session["user_id"] = sqldata[0][0]
        return redirect("/menu")
    else:
        return render_template("login.html", alert="")

@app.route("/register", methods=["POST", "GET"])
def register():
    connection = sqlite3.connect("data.db")
    crsr = connection.cursor()
    if request.method == "POST":
        if request.form["submitbutton"] == "register":
            username = request.form.get("username").lower()
            password = request.form.get("password")
            passwordconf = request.form.get("passwordconf")
            if len(username) > 255 or len(password) > 255:
               return render_template("register.html", alert="Username or password has more than 255 digits")
            if username == "":
                return render_template("register.html", alert="Enter a valid username")
            if password == "":
                return render_template("register.html", alert="Enter a valid password")
            if passwordconf == "":
                return render_template("register.html", alert="Enter a valid confirmation password")
            for char in username:
                if char == " ":
                    return render_template("register.html", alert="Username can't contain spaces")
            for char in password:
                if char == " ":
                    return render_template("register.html", alert="Password can't contain spaces")
            if passwordconf != password:
                return render_template("register.html", alert="Passwords don't match")  
            if len(username) < 6:
                    return render_template("register.html", alert="Username can't be less than 6 digits")
            if len(password) < 6:
                    return render_template("register.html", alert="Password can't be less than 6 digits")

            crsr.execute("SELECT username FROM users WHERE username=:username;", {"username": username})
            sqldata = crsr.fetchall()
            if len(sqldata) != 0:
                return render_template("register.html", alert="Username is already taken")
            crsr.execute("INSERT INTO users (username, password) VALUES (:username, :password);", {"username": username, "password": password})
            crsr.execute("SELECT id FROM users WHERE username=:username;", {"username": username})
            sqldata = crsr.fetchall()
            session["user_id"] = sqldata[0][0]
            query = "INSERT INTO config (id, backgroundcolor, dcover, dcunder, withscore, riskscore, onlylose, onlywin, double3, double4, doublelose, winscore, losescore, wincouples, losecouples, dcoverlose, dcunderlose) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, 0, 10, 10, 33, 33);"
            crsr.execute(query, {"1": session["user_id"], "2": "white", "3": 33, "4": 33, "5": 10, "6": 10, "7": 10, "8": 10, "9": "true", "10": "true", "11": "true", "12": 10})
            connection.commit()
            return redirect("/menu")
        else:
            return redirect("/")
    else:
        alert = ""
        return render_template("register.html", alert=alert)

@app.route("/menu", methods=["POST", "GET"])
def menu():
    if session.get('user_id') is None:
        return redirect("/")
    if request.method == "POST":
        if request.form['submitbutton'] == "solo":
            session["type"] = "Solo"
            session["round"] = 0
            session["alllose"] = "false"
            session["current"] = 0
            return redirect("/calculator")
        elif request.form['submitbutton'] == "back":
            session.clear()
            return redirect("/")
        elif request.form["submitbutton"] == "couples":
            session["type"] = "Couples"
            session["round"] = 0
            session["alllose"] = "false"
            session["current"] = 0
            return redirect("/calculator")
        else:
            return redirect("load")
    else:
        connection = sqlite3.connect("data.db")
        crsr = connection.cursor()
        crsr.execute("SELECT backgroundcolor FROM config WHERE id = :id", {"id": session["user_id"]})
        sqldata = crsr.fetchall()
        return render_template("menu.html", background=sqldata[0][0])


@app.route("/load", methods=["POST", "GET"])
def loadbola():
    if session.get('user_id') is None:
        return redirect("/")
    if request.method == "POST":
        if request.form['submitbutton'] == "back":
            return redirect("/menu")
        connection = sqlite3.connect("data.db")
        crsr = connection.cursor()
        crsr.execute("SELECT bolas_id, player1, player2, player3, player4, type FROM bolas WHERE id = :id", {"id": session["user_id"]})
        bolas = crsr.fetchall()
        bolaid = request.form.get("bolaid")
        crsr.execute("SELECT backgroundcolor FROM config WHERE id = :id", {"id": session["user_id"]})
        sqldata = crsr.fetchall()
        
        if not bolaid.isnumeric():
            alert = "ID must be a number"
            return render_template("load.html", alert=alert, bolas=bolas, background=sqldata[0][0])

        crsr.execute("SELECT id, type FROM bolas WHERE bolas_id = :id", {"id": bolaid})
        bolass = crsr.fetchall()

        if len(bolass) != 0:
            if bolass[0][0] != session["user_id"]:
                alert = "You do not have access to this game"
                return render_template("load.html", alert=alert, bolas=bolas, background=sqldata[0][0])
        else:
            alert = "This game does not exist"
            return render_template("load.html", alert=alert, bolas=bolas, background=sqldata[0][0])
            
        if  request.form["submitbutton"] == "delete":
            crsr.execute("DELETE FROM bolas WHERE id=:id AND bolas_id=:bola", {"id": session["user_id"], "bola": bolaid})
            connection.commit()
            return redirect("/load")

        session["type"] = bolass[0][1]
        session["current"] = bolaid
        session["alllose"] = "false"
        crsr.execute("SELECT max(round) FROM rounds WHERE bolas_id = :id", {"id": bolaid})
        bolas = crsr.fetchall()
        session["round"] = bolas[0][0]
        return redirect("/calculator")
    else:
        connection = sqlite3.connect("data.db")
        crsr = connection.cursor()
        crsr.execute("SELECT backgroundcolor FROM config WHERE id = :id", {"id": session["user_id"]})
        sqldata = crsr.fetchall()
        crsr.execute("SELECT bolas_id, player1, player2, player3, player4, type FROM bolas WHERE id = :id", {"id": session["user_id"]})
        bolas = crsr.fetchall()
        alert = ""
        return render_template("load.html", alert=alert, bolas=bolas, background=sqldata[0][0])


@app.route("/calculator", methods=["POST", "GET"])
def calculator():
    if session.get('user_id') is None:
        return redirect("/")
    if session.get('type') is None:
        return redirect("/menu")
    if request.method == "POST": 
        connection = sqlite3.connect("data.db")
        crsr = connection.cursor()

        if request.form["submit"] == "back":
            return redirect("/menu")

        if session.get("round") is None:
            session["round"] = 0

        if  request.form["submit"] == "delete":
            crsr.execute("DELETE FROM rounds WHERE id=:id AND bolas_id=:bola AND round=:r", {"id": session["user_id"], "bola": session["current"], "r": session["round"]})
            connection.commit()
            if session["round"] > 0:
                session["round"] -= 1
            return redirect("/calculator")

        acond = True

        if request.form["submit"] == "save":
            acond = False
        
        sc = request.form
        WITHRISKDC = sc.get("elements")
        conditions = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        counter = 0
        
        names = [sc.get("name1"), sc.get("name2"), sc.get("name3"), sc.get("name4")]

        for char in WITHRISKDC:
            if char != " ":
                conditions[counter] += char
            if char == " ":
                counter += 1

        WITH = [conditions[0], conditions[3], conditions[6], conditions[9]]
        RISK = [conditions[1], conditions[4], conditions[7], conditions[10]]
        DC = [conditions[2], conditions[5], conditions[8], conditions[11]]
        DOUBLE3 = conditions[12]
        DOUBLE4 = conditions[13]
        DOUBLELOSE = conditions[14]
        COLOR = conditions[15]
        CUT = conditions[16]

        if session["current"] == 0 and acond:
            crsr.execute("INSERT INTO bolas (id, player1, player2, player3, player4, type) VALUES (:id, :1, :2, :3, :4, :5);", {"id": session["user_id"], "1": names[0], "2": names[1], "3": names[2], "4": names[3], "5": session["type"]})
            connection.commit()

        if session["current"] == 0 and acond:
            crsr.execute("SELECT max(bolas_id) FROM bolas WHERE id=:id", {"id": session["user_id"]})
            bolasmax = crsr.fetchall()
            session["current"] = bolasmax[0][0]

        crsr.execute("SELECT player1, player2, player3, player4 FROM bolas WHERE bolas_id=:1 AND id=:2", {"1": session["current"], "2": session["user_id"]})
        namessql = crsr.fetchall()
        cond = False
        if acond:
            for i in range(len(namessql[0])):
                if names[i] != namessql[0][i]:
                    cond = True

        if cond:
            query = "UPDATE bolas SET player1=:1, player2=:2, player3=:3, player4=:4 WHERE id=:5 AND bolas_id=:6"
            crsr.execute(query, {"1": names[0], "2": names[1], "3": names[2], "4": names[3], "5": session["user_id"], "6": session["current"] } )
            connection.commit()

        crsr.execute("SELECT score1, score2, score3, score4, call1, call2, call3, call4, got1, got2, got3, got4, cut, round, overunder FROM rounds WHERE id=:id AND bolas_id=:1", {"id": session["user_id"], "1": session["current"]})
        rounds = crsr.fetchall()
        crsr.execute("SELECT * FROM config WHERE id = :id", {"id": session["user_id"]})
        config = crsr.fetchall()
        WITHVALUE = sc.get("withvalue")
        RISKVALUE = sc.get("riskvalue")
        ONLYLOSE = sc.get("onlylose")
        ONLYWIN = sc.get("onlywin")
        DCOVER = sc.get("dcover")
        DCUNDER = sc.get("dcunder")
        WINVALUE = sc.get("winvalue")
        LOSEVALUE = sc.get("losevalue")
        WINCOUPLES = sc.get("wincouples")
        LOSECOUPLES = sc.get("losecouples")
        DCOVERLOSE = sc.get("dcoverlose")
        DCUNDERLOSE = sc.get("dcunderlose")

        if request.form["submit"] == "save":
            if not sc.get("losevalue").isnumeric() or not sc.get("losecouples").isnumeric() or not sc.get("wincouples").isnumeric() or not sc.get("dcunderlose").isnumeric() or not sc.get("dcoverlose").isnumeric() or not sc.get("winvalue").isnumeric() or not sc.get("withvalue").isnumeric() or not sc.get("riskvalue").isnumeric() or not sc.get("onlylose").isnumeric() or not sc.get("onlywin").isnumeric() or not sc.get("dcover").isnumeric() or not sc.get("dcunder").isnumeric():
                alert = "Wrong settings"
                return render_template("calculator.html", bola=session["type"], name1 = names[0], name2 = names[1], name3 = names[2], name4 = names[3], rounds = rounds, alert=alert, color=config[0][1], dcover=config[0][2], dcunder=config[0][3], withvalue=config[0][4], riskvalue=config[0][5], onlylose=config[0][6], onlywin=config[0][7], double3=config[0][8], double4=config[0][9], doublelose=config[0][10], winvalue=config[0][11], losevalue=config[0][12], wincouples=config[0][13], losecouples=config[0][14], dcoverlose=config[0][15], dcunderlose=config[0][16])
            query = "UPDATE config SET backgroundcolor=:11, dcover=:2, dcunder=:3, withscore=:4, riskscore=:5, onlylose=:6, onlywin=:7, double3=:8, double4=:9, doublelose=:10, winscore=:12, losescore=:13, wincouples=:14, losecouples=:15, dcoverlose=:16, dcunderlose=:17 WHERE id=:1;"
            crsr.execute(query, {"1": session["user_id"], "2": DCOVER, "3": DCUNDER, "4": WITHVALUE, "5": RISKVALUE, "6": ONLYLOSE, "7": ONLYWIN, "8": DOUBLE3, "9": DOUBLE4, "10": DOUBLELOSE, "11": COLOR, "12":WINVALUE, "13":LOSEVALUE, "14":WINCOUPLES, "15":LOSECOUPLES, "16":DCOVERLOSE, "17":DCUNDERLOSE})
            connection.commit()
            return redirect("/calculator")
        
        WITHVALUE = int(sc.get("withvalue"))
        RISKVALUE = int(sc.get("riskvalue"))
        ONLYLOSE = int(sc.get("onlylose"))
        ONLYWIN = int(sc.get("onlywin"))
        DCOVER = int(sc.get("dcover"))
        DCUNDER = int(sc.get("dcunder"))
        WINVALUE = int(sc.get("winvalue"))
        LOSEVALUE = int(sc.get("losevalue"))
        WINCOUPLES = int(sc.get("wincouples"))
        LOSECOUPLES = int(sc.get("losecouples"))
        DCOVERLOSE = int(sc.get("dcoverlose"))
        DCUNDERLOSE = int(sc.get("dcunderlose"))
        
        CALL = [sc.get("call1"), sc.get("call2"), sc.get("call3"), sc.get("call4")]
        GOT = [sc.get("got1"), sc.get("got2"), sc.get("got3"), sc.get("got4")]

        alert = errorchecking1(CALL, GOT)
        if alert != "":
            return render_template("calculator.html", bola=session["type"], name1 = names[0], name2 = names[1], name3 = names[2], name4 = names[3], rounds = rounds, alert=alert, color=config[0][1], dcover=config[0][2], dcunder=config[0][3], withvalue=config[0][4], riskvalue=config[0][5], onlylose=config[0][6], onlywin=config[0][7], double3=config[0][8], double4=config[0][9], doublelose=config[0][10], winvalue=config[0][11], losevalue=config[0][12], wincouples=config[0][13], losecouples=config[0][14], dcoverlose=config[0][15], dcunderlose=config[0][16])
            
        CALLINT = [int(sc.get("call1")), int(sc.get("call2")), int(sc.get("call3")), int(sc.get("call4"))]
        GOTINT = [int(sc.get("got1")), int(sc.get("got2")), int(sc.get("got3")), int(sc.get("got4"))]
        sumcall = 0
        sumgot = 0
        call = 0    
        count = 0
        win = [False, False, False, False]
        callscounter = 0

        for i in range(4):
            sumcall += CALLINT[i]
            sumgot += GOTINT[i]
            if CALLINT[i] == 0:
                count += 1
            if CALLINT[i] > call:
                call = CALLINT[i]
            if CALLINT[i] == GOTINT[i]:
                win[i] = True
            if DC[i] == "true":
                count += 1

        for i in range(4):
            if CALLINT[i] == call:
                WITH[i] = "true"
            if WITH[i] == "true":
                callscounter += 1
            elif RISK[i] == "true":
                callscounter += 1
                if (sumcall > 13):
                    x = sumcall - 13
                else:
                    x = 13 - sumcall
                if x == 1:
                    RISK[i] = "false"
            elif DC[i] == "true":
                callscounter += 1
        double = 0

        if callscounter == 3 and DOUBLE3 == "true":
            double = 1
        if callscounter == 4 and DOUBLE4 == "true":
            double = 1
            
        alert = errorchecking2(sumcall, sumgot, count, WITH, RISK, DC, CALLINT)

        if alert != "":
            return render_template("calculator.html", bola=session["type"], name1 = names[0], name2 = names[1], name3 = names[2], name4 = names[3], rounds = rounds, alert=alert, color=config[0][1], dcover=config[0][2], dcunder=config[0][3], withvalue=config[0][4], riskvalue=config[0][5], onlylose=config[0][6], onlywin=config[0][7], double3=config[0][8], double4=config[0][9], doublelose=config[0][10], winvalue=config[0][11], losevalue=config[0][12], wincouples=config[0][13], losecouples=config[0][14], dcoverlose=config[0][15], dcunderlose=config[0][16])
        scores = [0, 0, 0, 0]
        scores = calculate(LOSECOUPLES, WINCOUPLES, DCUNDERLOSE, DCOVERLOSE, LOSEVALUE, WINVALUE, WITH, RISK, DC, win, scores, double, CALLINT, GOTINT, sumcall, RISKVALUE, WITHVALUE, DCUNDER, DCOVER, ONLYWIN, ONLYLOSE)
        crsr.execute("SELECT score1, score2, score3, score4, alllose FROM rounds WHERE id=:id AND bolas_id=:1 AND round=:r", {"id": session["user_id"], "1": session["current"], "r": (session["round"])})
        oldscores = crsr.fetchall()
        session["round"] += 1


        if len(oldscores) == 0:
            lastscores = [0, 0, 0, 0]
        else:
            lastscores = [int(oldscores[0][0]), int(oldscores[0][1]), int(oldscores[0][2]), int(oldscores[0][3])]
            if oldscores[0][4] == "true" and DOUBLELOSE == "true":
                for i in range(4):
                    scores[i] *= 2
        
        if (sumcall > 13):
            overunder = ("+" + str(sumcall - 13)) 
        else:
            overunder = ("-" + str(13 - sumcall)) 

        query = "INSERT INTO rounds (bolas_id, round, score1, score2, score3, score4, id, call1, call2, call3, call4, got1, got2, got3, got4, alllose, cut, overunder) VALUES (:1, :2, :3, :4, :5, :6, :id, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17);"
        crsr.execute(query, {"id": session["user_id"], "1": session["current"], "2": session["round"], "3": scores[0]+lastscores[0], "4": scores[1]+lastscores[1], "5": scores[2]+lastscores[2], "6": scores[3]+lastscores[3], "7": CALLINT[0], "8": CALLINT[1], "9": CALLINT[2], "10": CALLINT[3], "11": GOTINT[0], "12": GOTINT[1], "13": GOTINT[2], "14": GOTINT[3], "15": session["alllose"], "16": CUT, "17": overunder})
        connection.commit()
        session["alllose"] = "false"
        crsr.execute("SELECT score1, score2, score3, score4, call1, call2, call3, call4, got1, got2, got3, got4, cut, round, overunder FROM rounds WHERE id=:id AND bolas_id=:1", {"id": session["user_id"], "1": session["current"]})
        rounds = crsr.fetchall()
        
        return render_template("calculator.html", bola=session["type"], name1 = names[0], name2 = names[1], name3 = names[2], name4 = names[3], rounds = rounds, alert=alert, color=config[0][1], dcover=config[0][2], dcunder=config[0][3], withvalue=config[0][4], riskvalue=config[0][5], onlylose=config[0][6], onlywin=config[0][7], double3=config[0][8], double4=config[0][9], doublelose=config[0][10], winvalue=config[0][11], losevalue=config[0][12], wincouples=config[0][13], losecouples=config[0][14], dcoverlose=config[0][15], dcunderlose=config[0][16])      
    else:
        alert = ""
        connection = sqlite3.connect("data.db")
        crsr = connection.cursor()
        crsr.execute("SELECT * FROM config WHERE id = :id", {"id": session["user_id"]})
        config = crsr.fetchall()
        crsr.execute("SELECT player1, player2, player3, player4 FROM bolas WHERE bolas_id=:1 AND id=:2", {"1": session["current"], "2": session["user_id"]})
        namessql = crsr.fetchall()
        crsr.execute("SELECT score1, score2, score3, score4, call1, call2, call3, call4, got1, got2, got3, got4, cut, round, overunder FROM rounds WHERE id=:id AND bolas_id=:1", {"id": session["user_id"], "1": session["current"]})
        rounds = crsr.fetchall()
        names = []
        if len(namessql) != 0:
            l = len(namessql[0])
        else:
            l = 0
            names = ["", "", "", ""]
        for i in range(l):
            names.append(namessql[0][i])
        
        return render_template("calculator.html", bola=session["type"], name1 = names[0], name2 = names[1], name3 = names[2], name4 = names[3], rounds = rounds, alert=alert, color=config[0][1], dcover=config[0][2], dcunder=config[0][3], withvalue=config[0][4], riskvalue=config[0][5], onlylose=config[0][6], onlywin=config[0][7], double3=config[0][8], double4=config[0][9], doublelose=config[0][10], winvalue=config[0][11], losevalue=config[0][12], wincouples=config[0][13], losecouples=config[0][14], dcoverlose=config[0][15], dcunderlose=config[0][16])

def risk(i, RISK, RISKVALUE, sumcall):
    if sumcall > 13:
        x = sumcall - 13
    else:
        x = 13 - sumcall
    if RISK[i] == "true":
        if x <= 3: 
            return RISKVALUE
        elif x <= 5:
            return RISKVALUE*2
        else:
            return RISKVALUE*3
    else:
        return 0

def onlywinlose(win):
    wins = 0
    loses = 0
    indexwinlose = [10, 10]
    for i in range(4):
        if win[i] == True:
            wins += 1
        if win[i] == False:
            loses += 1
    if wins == 1:
        for i in range(4):
            if win[i] == True:
                indexwinlose[0] = i
    if loses == 1:
        for i in range(4):
            if win[i] == False:
                indexwinlose[1] = i
    return indexwinlose


def calculate(LOSECOUPLES, WINCOUPLES, DCUNDERLOSE, DCOVERLOSE, LOSEVALUE, WINVALUE, WITH, RISK, DC, win, scores, double, CALLINT, GOTINT, sumcall, RISKVALUE, WITHVALUE, DCUNDER, DCOVER, ONLYWIN, ONLYLOSE):
    indexwinlose = onlywinlose(win)
    losecounter = 0
    for i in range(4):
        if win[i] == True:
            if (CALLINT[i] >= 8):
                scores[i] += CALLINT[i]*CALLINT[i] 
                scores[i] += risk(i, RISK, RISKVALUE, sumcall)
            elif WITH[i] == "false" and DC[i] == "false":
                scores[i] += risk(i, RISK, RISKVALUE, sumcall)
                scores[i] += CALLINT[i]
                scores[i] += WINVALUE
            elif DC[i] == "true":
                if (sumcall > 13):
                    scores[i] += DCOVER
                else:
                    scores[i] += DCUNDER
            elif WITH[i] == "true":
                scores[i] += risk(i, RISK, RISKVALUE, sumcall)
                scores[i] += WITHVALUE
                scores[i] += CALLINT[i]
                scores[i] += WINVALUE
            if (indexwinlose[0] != 10) and indexwinlose[0] == i and session["type"] == "Solo":
                scores[i] += ONLYWIN
            if double == 1:
                scores[i] *= 2
        elif win[i] == False:
            if (CALLINT[i] > 8):
                scores[i] -= ((CALLINT[i]*CALLINT[i]) / 2)
                scores[i] -= risk(i, RISK, RISKVALUE, sumcall)
            elif WITH[i] == "false" and DC[i] == "false":
                scores[i] -= risk(i, RISK, RISKVALUE, sumcall)
                scores[i] -= LOSEVALUE
                if CALLINT[i] > GOTINT[i]:
                    scores[i] -= (CALLINT[i] - GOTINT[i])
                else:
                    scores[i] -= (GOTINT[i] - CALLINT[i])
            elif DC[i] == "true":
                if (sumcall > 13):
                    scores[i] -= DCOVERLOSE
                else:
                    scores[i] -= DCUNDERLOSE
            elif WITH[i] == "true":
                scores[i] -= risk(i, RISK, RISKVALUE, sumcall)
                scores[i] -= WITHVALUE
                scores[i] -= LOSEVALUE
                if CALLINT[i] > GOTINT[i]:
                    scores[i] -= (CALLINT[i] - GOTINT[i])
                else:
                    scores[i] -= (GOTINT[i] - CALLINT[i])
            if (indexwinlose[1] != 10) and indexwinlose[1] == i and session["type"] == "Solo":
                scores[i] -= ONLYLOSE
            if double == 1:
                scores[i] *= 2
            losecounter += 1
    if losecounter == 4:
        scores = [0, 0, 0, 0]
        session["alllose"] = "true"
    if session["type"] == "Couples":
        if win[0] == True and win[2] == True:
            scores[0] += WINCOUPLES
        if win[1] == True and win[3] == True:
            scores[1] += WINCOUPLES
        if win[0] == False and win[2] == False:
            scores[0] -= LOSECOUPLES
        if win[1] == False and win[3] == False:
            scores[0] -= LOSECOUPLES

    return scores

def errorchecking1(CALL, GOT):
    for i in range(4):
        if not CALL[i].isnumeric() or not GOT[i].isnumeric():
            alert="Please enter positive numbers"
            return alert

    alert=""
    return alert

def errorchecking2(sumcall, sumgot, count, WITH, RISK, DC, CALLINT):
    if sumcall == 13:
        alert="The sum of wanted tricks can not be 13"
        return alert
        
    if sumgot != 13:
        alert="The sum of collected tricks can not be less or greater than 13"
        return alert
        
    if sumcall < 0:
        alert="The sum of wanted tricks can not be less than 0"
        return alert
    
    if count > 2:
        alert="Only two players can dash"
        return alert
    
    if sumcall > 13:
        x = sumcall - 13
    else:
        x = 13 - sumcall

    sumrisk = 0

    for i in range(4):
        if DC[i] == "true":
            if WITH[i] == "true":
                alert="You can not be dash call and with at the same time"
                return alert
            if RISK[i] == "true":
                alert="You can not be dash call and risk at the same time"
                return alert
            if CALLINT[i] != 0:
                alert="DC calls 0 tricks"
                return alert
        if RISK[i] == "true":
            sumrisk += 1

    if sumrisk > 1:
        alert="Only one player can be risk"
        return alert

    if sumrisk == 0 and x != 1:
        alert="The game is risk"
        return alert

    alert=""
    return alert

if __name__ == "__main__":
    app.run()