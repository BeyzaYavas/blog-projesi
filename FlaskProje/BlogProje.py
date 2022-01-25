
from flask import Flask,render_template,flash,redirect,url_for,request,session,logging
#from flaskext.mysql import MySQL 
from flask_mysqldb import MySQL 
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
#import MySQLdb
from functools import wraps

#Kullanıcı Giriş Decorator Control:
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: 
            return f(*args, **kwargs)

        else:
            flash("Bu sayfayı görüntüleyebilmek için lütfen giriş yapınız...","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kullanıcı Kayıt Formu:
class RegisterForm(Form): #WTFormdan inherit edildi.
    name =StringField("İsim Soyisim", validators=[validators.Length(min=4,max=25)])
    username =StringField("Kullanıcı Adı", validators=[validators.Length(min=3,max=30),validators.DataRequired(message="Bu alanın girilmesi zorunludur.")])
    email =StringField("Email Adresi", validators=[validators.Email(message="Lütfen Geçerli Bir Email Adresi Giriniz...")])
    password =PasswordField("Parola", validators=[
        validators.DataRequired(message="Bir Parola Belirleyiniz."),
        validators.EqualTo(fieldname="confirm",message=" Parolanız Uyuşmuyor...")])

    confirm = PasswordField("Parolanızı Doğrulayın")
    
#Kullanıcı Girişi Yapma Formu:
class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")

#Makale Formu:
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

app=Flask(__name__)
app.secret_key="byblog"

#mysql konfigürasyonları
app.config["MYSQL_HOST"]="localhost"  #"127.0.0.1:5000"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="byblog" 
app.config["MYSQL_CURSORCLASS"]="DictCursor" 

mysql=MySQL(app)

@app.route("/")
def index():
    return render_template("index5.html")

@app.route("/about")
def about():
    return render_template("about.html")

#Makale Sayfası:
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles"
    #eğer db de hiçbir makale yoksa result 0 dır
    result = cursor.execute(sorgu)
    if result > 0 :
        articles=cursor.fetchall() #tüm makaleleri liste içinde sözlük yapısıyla verir.
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu ="Select * From articles where author=%s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else :
        return render_template("dashboard.html")

#Detay Sayfası
@app.route("/article/<string:id>") #dinamik url yapısı
def detail(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0 :
        article = cursor.fetchone() #id primary key olduğundan bir id den birden fazla bulunmuyor.
        return render_template("detail.html",article=article)
    else :
        return render_template("detail.html") 

#login 
@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method =="POST"and form.validate():
        username=form.username.data
        password_entered=form.password.data

        cursor = mysql.connection.cursor()
        sorgu="Select * From users Where username = %s"
        #eğer böyle bir kullanıcı db de yoksa result=0 olur.
        result = cursor.execute(sorgu,(username,)) 

        if result > 0:
            datas= cursor.fetchone() #tüm dataları almak için
            real_password=datas["password"]

            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarılı Giriş...","success")

                session["logged_in"]=True
                session["username"]=username

                return redirect(url_for("index"))
            else:
                flash("Parola Yanlış...","danger")
                return redirect(url_for("login"))    
        
        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor...","danger")
            return redirect(url_for("login"))


    return render_template("login.html",form = form)

#register
@app.route("/register",methods=["GET","POST"]) #hem get hem de post request alabilecek
def register():
    form = RegisterForm(request.form) #oluşturduğumuz kullanıcı kayıt formundan bir form objesi oluşturduk
    
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

    #phpMyAdmin de işlem yapmak için gerekli olan cursorü oluşturuyoruz.
        cursor=mysql.connection.cursor()
        #cursor = mysql.get_db().cursor()
        sorgu= "Insert into users(name,email,username,password) Values(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit() #veritabanında herhangi bir değişiklik yaptığımızda commit yapmamız gerekiyor.
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)

#Çıkış Yapma:
@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış Yapıldı...","danger")
    return redirect(url_for("index"))

#Makale Ekleme:
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method =="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        author=session["username"]

        cursor=mysql.connection.cursor()
        sorgu="Insert into articles(title,author,content) Values(%s,%s,%s)"
        cursor.execute(sorgu,(title,author,content))
        mysql.connection.commit()
        cursor.close()

        flash("Makaleniz Başarıyla Eklendi...","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html",form=form)

#Makale Silme:
@app.route("/delete/<string:id>")
@login_required
def delete(id): #dinamik url yapısı
    cursor = mysql.connection.cursor()
    sorgu ="Select * From articles where author = %s and id = %s "
    result= cursor.execute(sorgu,(session["username"],id))

    if result > 0: 
        #böyle bir makale varsa ve bu kullanıcıya aitse silme yapılacak
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        #bu sorgu db de değişiklik yaptığı için commit() işlemi yapmalıyız
        mysql.connection.commit()
        flash("Makale başarıyla silindi...","warning")
        return redirect(url_for("dashboard"))

    else: 
        flash("Bu makale yok veya bu işlem için yetkiniz yok...","danger")
        return redirect(url_for("index"))

#Makale Güncelleme:
@app.route("/edit/<string:id>", methods=["GET","POST"])
@login_required
def update(id):
    # get request yapıldığında articleform ile eski bilgileri kullanıcaz fakat post request yapıldığında formun güncellenmiş halini vermemiz lazım.
    if request.method == "GET":
        #ilk olarak db deki mevcut bilgileri çekmemiz lazım.
        cursor = mysql.connection.cursor()
        sorgu1= "Select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu1,(id,session["username"]))
        if result == 0:
            #makalenin db de bulunup kullanıcıya ait olmama durumu veya db de hiç olmama durumu
            flash("Böyle bir makale yok veya bu işlem için yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            #makale mevcut ve kullanıcıya ait
            article = cursor.fetchone() #makale bilgilerinin şuanki hali
            form = ArticleForm() #request.form yapmadık çünkü var olan bilgilerle formu oluşturacağız.

            form.title.data = article["title"]
            form.content.data =article["content"]

            return render_template("update.html",form=form)

    else:  
        #güncelle butonuna basılınca post request yapıyoruz.
        #post request:
        form = ArticleForm(request.form)

        newTitle=form.title.data
        newContent=form.content.data

        sorgu2="Update articles Set title = %s, content=%s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale başarıyla güncellendi...","success")

        return redirect(url_for("dashboard"))

#Arama Url:
@app.route("/search", methods=["GET","POST"]) #bu sayfa için hem get hemde post request gelebilir.
def search():
    # ancak bu sayfayı sadece post request oldugunda göstermemiz gerek yani yalnızca ara butonuna basıldıgında 
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword") #search engine kısmına yazılan kelimeyi alıyoruz.(input alanının name i)
        
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%"+ keyword +"%' "
        result=cursor.execute(sorgu)

        if result > 0: 
            articles = cursor.fetchall()
            return render_template("articles.html",articles=articles)

        else:     #aradığımız kelimeyi içeren bir makale bulunmuyor
            flash("Aradığınız kelimeyi içeren bir makale bulunmamaktadır...","warning")
            return redirect(url_for("articles"))

        

if __name__=="__main__":
    app.run(debug=True)