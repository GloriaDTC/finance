# C.S.50 Finance | Mock Stock Trading Platform

A robust, full-stack web application that allows users to manage a virtual investment portfolio, fetch real-time stock market data, and execute simulated trades.

## 📌 Project Overview
Developed as part of the **Harvard CS50x** curriculum, this project focuses on building a data-driven web application using **Python** and **Flask**. It bridges the gap between backend logic and database management, ensuring secure user authentication and consistent financial transaction processing.

## 🛠️ Tech Stack
* **Backend:** Python 3, Flask (Web Framework)
* **Database:** SQL (SQLite3)
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 (Templating Engine)
* **API:** IEX Cloud API (Real-time financial data)
* **Security:** Werkzeug (Password hashing), Flask-Session (Server-side session management)

## 🚀 Key Features
* **Secure Authentication:** User registration and login system with **PBKDF2 password hashing** to ensure data privacy.
* **Real-time Market Data:** Integration with the **IEX Cloud API** to retrieve live stock quotes and company information.
* **Portfolio Management:** * **Buy/Sell:** Automated calculation of transaction totals with real-time balance validation.
    * **Dynamic Dashboard:** Real-time rendering of current holdings, share prices, and total net worth (cash + stocks).
* **Transaction History:** A comprehensive audit trail recording every trade (symbol, shares, price, and timestamp).
* **Error Handling:** Robust backend validation for edge cases, such as insufficient funds, invalid stock symbols, or negative share inputs.

## 📁 Project Structure
```bash
.
├── app.py              # Main application logic & route controllers
├── helpers.py          # Auxiliary functions (API calls, login decorators)
├── finance.db          # SQL database storing users, portfolios, and logs
├── static/             # Static assets (CSS, images)
├── templates/          # Jinja2 HTML templates for the UI
└── requirements.txt    # Project dependencies
