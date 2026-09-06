# ATM Banking System

A web-based ATM banking application built with Flask. Users can create accounts, log in with a PIN, check balances, deposit and withdraw money, view transaction history, download receipts, and reset forgotten PINs using email OTP verification.

## Features

- User registration and login
- PIN-based authentication
- Account balance checking
- Cash deposits
- Cash withdrawals
- Transaction history
- PDF transaction receipts
- Forgot PIN functionality
- Email OTP verification
- PIN reset
- Session-based logout
- JSON file-based data storage
- Responsive frontend using HTML and CSS

## Technologies Used

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- JSON
- SMTP email service

## Project Structure

```text
ATM/
├── app.py
├── data.json
├── mail.py
├── requirements.txt
├── static/
│   ├── css/
│   └── js/
└── templates/
    ├── base.html
    ├── checkbalance.html
    ├── dashboard.html
    ├── deposit.html
    ├── forgotpin.html
    ├── login.html
    ├── register.html
    ├── resetpin.html
    ├── verify.html
    ├── viewtransactions.html
    └── withdraw.html

Requirements
Python 3.8 or later
pip
Gmail account or another SMTP email provider for OTP verification
