import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # 获取用户持有的股票信息
    stocks = db.execute("""
        SELECT symbol, SUM(shares) as total_shares
        FROM transactions
        WHERE user_id = :user_id
        GROUP BY symbol
        HAVING total_shares > 0
    """, user_id=session["user_id"])

    # 获取每只股票的当前价格并计算总价值
    holdings = []
    total_value = 0
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock_value = stock["total_shares"] * quote["price"]
        total_value += stock_value
        holdings.append({
            "symbol": stock["symbol"],
            "shares": stock["total_shares"],
            "price": quote["price"],
            "value": stock_value
        })

    # 获取用户的现金余额
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    total_value += cash

    return render_template("index.html", holdings=holdings, cash=cash, total_value=total_value)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # 获取表单数据
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # 确保股票代码和购买数量是有效的
        if not symbol:
            return apology("must provide symbol", 400)
        if not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("must provide a positive integer number of shares", 400)

        # 获取股票的当前价格
        quote = lookup(symbol.upper())
        if not quote:
            return apology("invalid symbol", 400)

        # 计算总购买价格
        total_cost = int(shares) * quote["price"]

        # 获取用户的当前现金余额
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

        # 检查用户是否有足够的现金
        if total_cost > user_cash:
            return apology("can't afford", 400)

        # 记录交易并更新用户的现金余额
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], symbol.upper(), int(shares), quote["price"])
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total_cost, session["user_id"])

        flash("Bought successfully!")
        return redirect("/")

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT symbol, shares, price, transacted FROM transactions WHERE user_id = :user_id ORDER BY transacted DESC",
                              user_id=session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("must provide symbol", 400)

        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", quote=quote)

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # 获取表单数据
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # 确保所有字段都已填写
        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if not confirmation:
            return apology("must confirm password", 400)

        # 确保密码与确认密码相符
        if password != confirmation:
            return apology("passwords do not match", 400)

        # 检查用户名是否已经存在
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                       username, generate_password_hash(password))
        except:
            return apology("username already exists", 400)

        # 获取新注册用户的 id 并记住用户
        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
        session["user_id"] = user_id

        # 注册成功后重定向到首页
        flash("Registered successfully!")
        return redirect("/")

    # 如果是 GET 请求，则显示注册表单
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not symbol or shares <= 0:
            return apology("must provide valid symbol and shares", 400)

        # 获取用户持有的股票数量
        stock = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id AND symbol = :symbol GROUP BY symbol",
                           user_id=session["user_id"], symbol=symbol)
        if len(stock) != 1 or stock[0]["total_shares"] < shares:
            return apology("not enough shares", 400)

        # 获取当前股票价格
        quote = lookup(symbol)

        # 计算总售价并更新用户现金余额
        total_sale = shares * quote["price"]
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_sale, session["user_id"])

        # 记录交易
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], symbol, -shares, quote["price"])

        flash("Sold successfully!")
        return redirect("/")

    # 获取用户持有的股票列表以填充表单
    stocks = db.execute("SELECT symbol FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING SUM(shares) > 0",
                        user_id=session["user_id"])
    return render_template("sell.html", stocks=stocks)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow user to change their password."""
    if request.method == "POST":
        # 获取用户输入的旧密码、新密码和确认密码
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # 检查所有字段是否已填写
        if not old_password or not new_password or not confirmation:
            return apology("must fill all fields", 403)

        # 查询数据库获取用户当前的密码哈希值
        user = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])

        # 验证旧密码是否正确
        if len(user) != 1 or not check_password_hash(user[0]["hash"], old_password):
            return apology("invalid old password", 403)

        # 确认新密码和确认密码是否匹配
        if new_password != confirmation:
            return apology("new passwords do not match", 403)

        # 更新数据库中的密码哈希值
        db.execute("UPDATE users SET hash = ? WHERE id = ?",
                   generate_password_hash(new_password), session["user_id"])

        # 向用户显示成功消息并重定向到主页
        flash("Password changed successfully")
        return redirect("/")

    # 如果是 GET 请求，渲染更改密码的表单
    return render_template("change_password.html")


@app.before_request
def setup():
    # 创建 transactions 表
    db.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        shares INTEGER NOT NULL,
        price REAL NOT NULL,
        transacted TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
