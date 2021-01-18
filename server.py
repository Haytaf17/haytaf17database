from flask import Flask, render_template, flash, redirect, url_for ,request ,session
from functools import wraps
import os
import psycopg2
dsn = os.getenv("DATABASE_URL")
#dsn = "user=postgres password=123456 host=127.0.0.1 port=5432 dbname=flaskdb"
con = psycopg2.connect(dsn)
cur = con.cursor()


app = Flask(__name__)
app.secret_key="hayta"
#Login control decorator / loginrequired / check login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You must be login to view this page.", "warning")
            return redirect(url_for("login_page"))

    return decorated_function


@app.route("/")
def home_page():
    cur = con.cursor()
    cur.execute("Select count(*) from users;")
    users=cur.fetchone()
    cur.execute("Select count(*) from product;")
    products=cur.fetchone()
    cur.execute("Select count(*) from evaluation;")
    evaluation=cur.fetchone()
    cur.execute("Select count(*) from company;")
    companies=cur.fetchone()
#    return render_template ('adminpanel.html',users=users,evaluation=evaluation,products=products,companies=companies)
    cur = con.cursor()
    cur.execute(" select users.email,product.productname,product.companyname,vote,comment ,reply from evaluation inner join users on evaluation.userid=users.userid inner join product on evaluation.productno=product.productno limit 5;")
    posts=cur.fetchall()
    cur.close()
    return render_template("main.html",posts=posts,users=users,evaluation=evaluation,products=products,companies=companies)

@app.route("/signup" ,methods=['GET','POST'])
def signup_page():
    if request.method == "GET":
        cur = con.cursor()
        cur.execute("Select companyname from company")
        companies=cur.fetchall()
        return render_template("signup.html",companies=companies)
    else:
        cur = con.cursor()
        mail=request.form['mail']
        password=request.form['password']
        usertype=request.form['question']
        companyname=request.form['companyname']
        if mail=='' or password=='':
            flash("Please enter your mail and password.","info")
            return redirect(url_for('signup_page'))
        cur.execute("Select * from users WHERE email ='{0}';".format(mail))
        data=cur.fetchone()
        cur.execute("Select * from companyaccount WHERE email ='{0}';".format(mail))
        data2=cur.fetchone()
        if(data):
            flash("Email already exists in users!","info")
            return redirect(url_for('signup_page'))
        elif (data2):
            flash("Email already exists in companyaccounts!","info")
            return redirect(url_for('signup_page'))
        else:
            if usertype=='customer':
                cur.execute("INSERT INTO users(email, password,IsAdmin,numberOfEvaluations) VALUES (%s,%s,0,0);",(mail,password) )
            else:
                cur.execute("select * from companyaccount where companyname='{0}';".format(companyname))
                exist=cur.fetchone()
                if exist:
                    flash("This company has an account!","info")
                    return redirect(url_for('signup_page'))
                else:
                    cur.execute("INSERT INTO companyaccount(companyname,email,password ) VALUES ('{0}','{1}','{2}');".format(companyname,mail,password))
        con.commit()
        cur.close()
        return redirect(url_for("home_page"))
    

@app.route("/newevaluation",methods=['GET','POST'])
def newevaluation_page():
    if request.method == "GET":
        cur = con.cursor()
        cur.execute("Select * from product ORDER BY productname ASC;")
        products=cur.fetchall()
        print(products)
        return render_template("newevaluation.html",products=products)
    else:
        cur = con.cursor()
        productno=request.form['productno']
        vote=request.form['vote']
        comment=request.form['comment']
        print(productno)
        UserID=session["UserID"]
        email=session["email"]
        cur.execute("INSERT INTO evaluation(UserID,ProductNo,Vote,Comment,Reply) VALUES (%s,%s,%s,%s,'');",(UserID,productno,vote,comment) )
        con.commit()
        cur.execute("UPDATE product SET (numberofvotes,score)=(numberofvotes+1,(score*numberofvotes+{0})/(numberofvotes+1)) WHERE productno ='{1}';".format(vote,productno))
        con.commit()
        cur.execute("SELECT *FROM company INNER JOIN product ON product.companyname = company.companyname WHERE product.productno='{0}';".format(productno))
        product_company=cur.fetchone()
        cur.execute("UPDATE company SET (numberofevaluations,averagescore)=(numberofevaluations+1,(averagescore*numberofevaluations+{0})/(numberofevaluations+1)) WHERE companyname ='{1}';".format(vote,product_company[0]))
        con.commit()
        cur.close() 
        return  redirect(url_for("home_page"))

@app.route("/newproduct",methods=['GET','POST'])
def newproduct():
    if request.method == "GET":
        return render_template("newproduct.html")
    else:
        cur = con.cursor()
        category=request.form['category']
        productname=request.form['productname']
        cur.execute("insert into product (productname,companyname,score,numberofvotes,categoryname) VALUES('{0}','{1}',0.0,0,'{2}');".format(productname,session["companyname"],category))
        con.commit()
        cur.execute("update company set numofproducts=numofproducts+1 where companyname='{0}';".format(session["companyname"]))
        con.commit()
        return redirect(url_for("companyprofile"))

@app.route("/login" ,methods=['GET','POST'])
def login_page():
    if request.method == "GET":
        return render_template("login.html")
    else:
        cur = con.cursor()
        mail=request.form['mail']
        password=request.form['password']
        if mail=='' or password=='':            
            return render_template('login.html',message='Please enter your mail and password.')
        cur.execute(" SELECT * FROM users WHERE email = '{0}';".format(mail))
        data=cur.fetchone()
        cur.execute(" SELECT * FROM companyaccount WHERE email = '{0}';".format(mail))
        data2=cur.fetchone()
        if(not data and not data2):
            return render_template ('login.html', message='This email is not registered. Please sign up from upper right')
        elif data:
            if data[2]==password:
                session["logged_in"] = True
                session["customer"] = True
                session["UserID"] = data[0]
                session["email"] = data[1]
                session["password"] = data[2]
                session["IsAdmin"] = data[3]
                cur.execute(" SELECT * FROM evaluation WHERE UserID='{0}' ;".format(data[0]))
                posts=cur.fetchall()
                return redirect(url_for('profile_page'))
            else:
                return render_template ('login.html', message='Check your password')
        else:
            if data2[2]==password:
                session["logged_in"] = True
                session["companyaccountid"] = data2[3]
                session["email"] = data2[1]
                session["companyname"] = data2[0]
                session["password"] = data2[2]
                return redirect (url_for("companyprofile"))
            else:
                return render_template ('login.html', message='Check your password')   
        con.commit()
        cur.close()
        return render_template("main.html")


@app.route('/logout')
@login_required
def logout_page():
    session.clear()
    flash("Logout success","info")
    return redirect(url_for("home_page"))

@app.route('/profile')
def profile_page():
    cur.execute("select evaluationid,userid, product.productname,vote,comment,reply from evaluation inner join product on evaluation.productno=product.productno WHERE UserID='{0}' ORDER by evaluationID ASC;".format(session["UserID"]))
    posts=cur.fetchall()
    return render_template ('profile.html' , posts=posts)

@app.route('/companyprofile',methods=['GET','POST'])
def companyprofile():
    if request.method =='GET':
        cur.execute("select * from product where companyname='{0}';".format(session["companyname"]))
        products=cur.fetchall()
        cur.execute("select evaluationid, users.email, product.productname,vote,comment,reply from evaluation inner join product on evaluation.productno=product.productno inner join users on evaluation.userid=users.userid where product.companyname='{0}'".format(session["companyname"]))
        posts=cur.fetchall()
        return render_template("companyprofile.html",posts=posts,products=products)
    if request.method =='POST':
        button=request.form['button']
        reply=request.form['reply']
        print(reply)
        cur.execute("UPDATE evaluation SET reply = '{0}' WHERE evaluationid='{1}';".format(reply,button))
        con.commit()
        return redirect(url_for('companyprofile'))

@app.route("/deleteproduct/<int:productno>")
def deleteproduct(productno):
    cur.execute("select * from product where productno='{0}';".format(productno))
    product=cur.fetchone()
    cur.execute(" DELETE FROM product WHERE productno = '{0}';".format(productno))
    con.commit()
    cur.execute(" Update company SET numofproducts=numofproducts-1 where companyname ='{0}';".format(product[2]))
    con.commit()
    return redirect(url_for('companyprofile'))
    
@app.route('/updateproduct/<int:productno>', methods=['GET', 'POST'])
def updateproduct(productno):
    if request.method == "GET":
        cur.execute(" SELECT * FROM product WHERE productno = '{0}';".format(productno))
        product=cur.fetchone()
        return render_template('updateproduct.html',values=product)
    else:
        productname=request.form['productname']
        category=request.form['category']
        cur.execute(" UPDATE  product SET productname='{0}',categoryname='{1}' where productno='{2}';".format(productname,category,productno))
        con.commit()
        return redirect(url_for('companyprofile'))

@app.route('/categoriestocompany/<categoryname>')
def categoriestocompany(categoryname):
    cur.execute("select companyname from product where categoryname='{0}';".format(categoryname))
    companies2=cur.fetchall()
    companies2 = list(dict.fromkeys(companies2))
    return render_template("companies.html",companies2=companies2)
      
@app.route("/companypage/<companyname>")
def companypage(companyname):
    cur.execute("Select * from company where companyname='{0}';".format(companyname))
    company=cur.fetchone()
    cur.execute("select count(*) from evaluation inner join product on evaluation.productno=product.productno where product.companyname='{0}' and evaluation.reply!=''".format(companyname))
    numofreply=cur.fetchone()
    cur.execute("select * from product where companyname='{0}';".format(companyname))
    products=cur.fetchall()
    return render_template('companypage.html',company=company,numofreply=numofreply ,products=products)
   
       

@app.route("/delete/<int:evaluation_id>")
@login_required
def deleteevaluation_page(evaluation_id):
    cur.execute(" SELECT * FROM evaluation WHERE evaluationID = '{0}' AND   userID = '{1}';".format(evaluation_id,session["UserID"]))
    evaluation =cur.fetchone()
    if evaluation:
        cur.execute(" DELETE FROM evaluation WHERE evaluationID = '{0}' AND   userID = '{1}';".format(evaluation_id,session["UserID"]))
        con.commit()
        cur.execute("select * from product where productno='{0}';".format(evaluation[2]))
        product=cur.fetchone()
        if product[4]!=1:
            cur.execute(" UPDATE PRODUCT SET (numberofvotes,score) = (numberofvotes-1,(numberofvotes*score-{0})/(numberofvotes-1)) where productno='{1}';".format(float(evaluation[3]),evaluation[2]))
            con.commit()
        else:
            cur.execute(" UPDATE PRODUCT SET (numberofvotes,score) = (numberofvotes-1,0) where productno='{0}';".format(evaluation[2]))
            con.commit()
        cur.execute("select * from company where companyname='{0}';".format(product[2]))
        company =cur.fetchone() 
        if company[3]!=1:
            cur.execute(" UPDATE COMPANY SET (numberofevaluations,averagescore) = (numberofevaluations-1,(numberofevaluations*averagescore-{0})/(numberofevaluations-1)) where companyname='{1}';".format(float(evaluation[3]),company[0]))
            con.commit()
        else:
            cur.execute(" UPDATE COMPANY SET (numberofevaluations,averagescore) = (numberofevaluations-1,0) where companyname='{0}';".format(company[0]))
            con.commit()
        #flash("Delete is success", "success")
        return redirect(url_for('profile_page'))
    flash("You are not authorized for this", "danger")
    return redirect(url_for('home_page'))



@app.route('/edit/<int:evaluation_id>', methods=['GET', 'POST'])
def editevaluation_page(evaluation_id):
    if request.method == "GET":
        cur.execute(" SELECT * FROM evaluation WHERE evaluationID = '{0}' AND  userID = '{1}';".format(evaluation_id,session["UserID"]))
        evaluation =cur.fetchone()
        cur.execute("Select * from product ORDER BY productname ASC;")
        products=cur.fetchall()
        return render_template('editevaluation.html',values=evaluation ,products=products)
    else:
        cur.execute(" SELECT * FROM evaluation WHERE evaluationID = '{0}' AND  userID = '{1}';".format(evaluation_id,session["UserID"]))
        evaluation =cur.fetchone()
        productno=request.form['productno']
        vote=request.form['vote']
        comment=request.form['comment']
        print(productno)
        UserID=session["UserID"]
        email=session["email"]
        cur.execute("UPDATE evaluation SET productno = '{0}' ,vote = {1} ,comment='{2}' WHERE evaluationid='{3}';".format(productno,int(vote),comment,evaluation_id))
        con.commit()
        cur.execute(" UPDATE product SET score = (score*numberofvotes-{0}+{1})/numberofvotes where productno='{2}';".format(int(evaluation[3]),int(vote),productno))
        con.commit()
        cur.execute("select * from product where productno='{0}';".format(productno))
        product=cur.fetchone()
        cur.execute(" UPDATE company SET averagescore = (averagescore*numberofevaluations-{0}+{1})/numberofevaluations where companyname='{2}';".format(int(evaluation[3]),int(vote),product[2]))
        con.commit()
        return redirect(url_for('profile_page'))

    
@app.route('/admin')
def admin_page():
    if session["IsAdmin"]==1:
        cur.execute("Select count(*) from users;")
        users=cur.fetchone()
        cur.execute("Select count(*) from product;")
        products=cur.fetchone()
        cur.execute("Select count(*) from evaluation;")
        evaluation=cur.fetchone()
        cur.execute("Select count(*) from company;")
        companies=cur.fetchone()
        return render_template ('adminpanel.html',users=users,evaluation=evaluation,products=products,companies=companies)
    else:
        return redirect(url_for('home_page'))
    
    
    
@app.route('/admin_companies',methods=['GET','POST'])
def admin_companies():
    if session["IsAdmin"]==1:
        if request.method == "GET":
            cur = con.cursor()
            cur.execute(" SELECT * FROM company ORDER BY companyname ASC;")
            companies=cur.fetchall()
            return render_template ('admin_companies.html' , companies=companies)
        else:
            cur = con.cursor()
            companyname=request.form['companyname']
            products=request.form['products']
            categories=request.form['categories']
            button=request.form['button']
            arr_products = products.split(",")
            arr_categories=categories.split(",")  
            if companyname=="":
                flash("Enter companyname!","info")
                return redirect(url_for("admin_companies"))
            if button=='0':
                cur.execute("select * from company where companyname='{0}';".format(companyname))
                data=cur.fetchall()
                if data:
                    flash("This company already exists!","info")
                    return redirect(url_for("admin_companies"))
                else:
                    if len(arr_categories) != len(arr_products):
                        flash("Number categories and products doesnt match!","info")
                        return redirect(url_for("admin_companies"))
                    else:
                        for i in range(len(arr_products)):
                            if arr_products[i]=="" or arr_categories[i]=="":
                                flash("Productname and categoryname shouldn't be empty!","info")
                                return redirect(url_for("admin_companies"))
                            cur.execute("INSERT INTO company(companyname,numofproducts,averagescore,numberofevaluations) VALUES ('{0}','{1}',0.0,0);".format(companyname,len(arr_products)))
                            con.commit()
                            for i in range(len(arr_products)):
                                cur.execute("INSERT INTO product(productname,companyname,score,numberofvotes,categoryname) VALUES ('{0}','{1}',0.0,0,'{2}');".format(arr_products[i],companyname,arr_categories[i]))
                                con.commit()
                            return redirect(url_for("admin_companies"))
            #update işlemleri
            
        

@app.route("/deletecompany/<companyname>")
@login_required
def deletecompany(companyname):
    cur.execute(" DELETE FROM company WHERE companyname = '{0}';".format(companyname))
    con.commit()
    return redirect(url_for('admin_companies'))

  
@app.route('/control_users',methods=['GET','POST'])
def control_users():
    if session["IsAdmin"]==1:
        cur = con.cursor()
        cur.execute(" SELECT * FROM users ORDER BY email ASC;")
        users=cur.fetchall()
        return render_template ('control_users.html' , users=users)
    else:
        return redirect(url_for('home_page'))



@app.route("/deleteuser/<int:userid>")
def deleteuser(userid):
    cur.execute(" DELETE FROM users WHERE userid= '{0}';".format(userid))
    con.commit()
    return redirect(url_for('control_users'))

@app.route("/makeadmin/<int:userid>")
def makeadmin(userid):
    cur.execute(" UPDATE users SET isadmin=1 WHERE userid='{0}';".format(userid))
    con.commit()
    return redirect(url_for('control_users'))

@app.route("/removeadmin/<int:userid>")
def removeadmin(userid):
    cur.execute(" UPDATE users SET isadmin=0 WHERE userid='{0}';".format(userid))
    con.commit()
    return redirect(url_for('control_users'))

@app.route("/adminevaluations")
def adminevaluations():
    if session["IsAdmin"]==1:
        cur.execute(" select evaluationid,users.email,product.productname,product.companyname,vote,comment ,reply from evaluation inner join users on evaluation.userid=users.userid inner join product on evaluation.productno=product.productno")
        evaluations=cur.fetchall()
        return render_template('adminevaluations.html',evaluations=evaluations)


@app.route("/adminevaluationdelete/<int:evaluationid>")
def adminevaluationdelete(evaluationid):
    if session["IsAdmin"]==1:
        cur.execute(" SELECT * FROM evaluation WHERE evaluationID = '{0}';".format(evaluationid))
        evaluation =cur.fetchone()
        if evaluation:
            cur.execute(" DELETE FROM evaluation WHERE evaluationID = '{0}';".format(evaluationid))
            con.commit()
            cur.execute("select * from product where productno='{0}';".format(evaluation[2]))
            product=cur.fetchone()
            if product[4]!=1:
                cur.execute(" UPDATE PRODUCT SET (numberofvotes,score) = (numberofvotes-1,(numberofvotes*score-{0})/(numberofvotes-1)) where productno='{1}';".format(float(evaluation[3]),evaluation[2]))
                con.commit()
            else:
                cur.execute(" UPDATE PRODUCT SET (numberofvotes,score) = (numberofvotes-1,0) where productno='{0}';".format(evaluation[2]))
                con.commit()
            cur.execute("select * from company where companyname='{0}';".format(product[2]))
            company =cur.fetchone() 
            if company[3]!=1:
                cur.execute(" UPDATE COMPANY SET (numberofevaluations,averagescore) = (numberofevaluations-1,(numberofevaluations*averagescore-{0})/(numberofevaluations-1)) where companyname='{1}';".format(float(evaluation[3]),company[0]))
                con.commit()
            else:
                cur.execute(" UPDATE COMPANY SET (numberofevaluations,averagescore) = (numberofevaluations-1,0) where companyname='{0}';".format(company[0]))
                con.commit()
            return redirect(url_for('adminevaluations'))
    flash("You are not authorized for this", "danger")
    return redirect(url_for('home_page'))

@app.route('/companies')
def companies_page():
    cur.execute(" SELECT * FROM company ORDER BY companyname DESC;")
    companies=cur.fetchall()
    return render_template ('companies.html')

@app.route('/products',methods=['GET','POST'])
def products_page():
    if request.method=='GET':
        cur.execute(" SELECT * FROM company ORDER BY companyname DESC;")
        companies=cur.fetchall()
        return render_template ('products.html')
    else :
        product=request.form['searchproduct']
        company=request.form['searchcompany']
        category=request.form['searchcategory']
        if request.form['button']=='1':
            button=request.form['button']
            cur.execute("select * from product;")
            products=cur.fetchall()
            return render_template ('products.html',products=products)
        else:
            if company=='' and category=='' and product=='':
                flash("Please enter at least one of them","info")
                return redirect(url_for('products_page'))
            else:
                cur.execute("select * from product WHERE productname LIKE '{0}%' and companyname LIKE '{1}%' and categoryname LIKE '{2}%';".format(product,company,category))
                products=cur.fetchall()
                return render_template ('products.html',products=products)


@app.route('/categories')
def categories():
    cur = con.cursor()
    cur.execute(" SELECT categoryname FROM product;")
    categories=cur.fetchall()
    print(categories)    
    categories = list(dict.fromkeys(categories))
    print(categories)
    return render_template('companies.html',categories=categories)

@app.route('/allcompanies')
def allcompanies():
    cur = con.cursor()
    cur.execute(" SELECT * FROM company ORDER BY companyname DESC;")
    companies=cur.fetchall()
    return render_template('companies.html',companies=companies)

@app.route('/topic')
def topic():
    cur = con.cursor()
    cur.execute(" SELECT * FROM company ORDER BY numberofevaluations DESC limit 5;")
    companies=cur.fetchall()
    return render_template('companies.html',companies=companies)
@app.route('/admired')
def admired():
    cur = con.cursor()
    cur.execute(" SELECT * FROM company ORDER BY averagescore DESC limit 5;")
    companies=cur.fetchall()
    return render_template('companies.html',companies=companies)



if __name__ == '__main__':
    app.debug=True
    app.run()
