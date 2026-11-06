import tkinter as tk
from tkinter import messagebox, simpledialog
import datetime
import json
import os
import hashlib
import secrets
import hmac

# GLOBAL VARIABLES
accounts = []
current_account = None
DATA_FILE = "Bankaccount.json"


# PASSWORD HASHING
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        200000
    )

    return salt, hashed.hex()


def verify_password(password, salt, stored_hash):
    _, entered_hash = hash_password(password, salt)
    return hmac.compare_digest(entered_hash, stored_hash)


# BANK ACCOUNT CLASS
class Bankaccount:

    def __init__(self, mname, maccount, mpassword,
                 memail, mphonenumber, salt=None,
                 stored_hash=None):

        self.mname = mname
        self.maccount = maccount
        self.memail = memail
        self.mphonenumber = mphonenumber

        if stored_hash is None:
            self.salt, self.password_hash = hash_password(
                mpassword, salt
            )
        else:
            self.salt = salt
            self.password_hash = stored_hash

        self.balance = 0
        self.mhistory = []

    def check_password(self, password):
        return verify_password(
            password,
            self.salt,
            self.password_hash
        )

    def info(self):
        return (
            f"Name: {self.mname}\n"
            f"Account: {self.maccount}\n"
            f"Email: {self.memail}\n"
            f"Phone: {self.mphonenumber}\n"
            f"Balance: ₹{self.balance}"
        )

    def deposit(self, amount):
        if amount <= 0:
            return "Invalid deposit amount!"

        self.balance += amount
        self.addlog("Deposit", "Cash Deposit", amount)

        return (
            f"Deposit amount: ₹{amount}\n"
            f"New balance: ₹{self.balance}"
        )

    def withdraw(self, amount):
        if amount <= 0:
            return "Invalid withdrawal amount!"

        if amount > self.balance:
            return "Insufficient balance!"

        self.balance -= amount
        self.addlog("Withdraw", "Cash Withdraw", amount)

        return (
            f"Withdraw amount: ₹{amount}\n"
            f"New balance: ₹{self.balance}"
        )

    def debit(self, amount):
        self.balance -= amount

    def credit(self, amount):
        self.balance += amount

    def checkbalance(self):
        return f"Your balance is: ₹{self.balance}"

    def addlog(self, operation, description, amount):
        transaction_id = len(self.mhistory) + 1

        date = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        self.mhistory.append([
            transaction_id,
            operation,
            description,
            amount,
            date
        ])


# OBJECT TO DICTIONARY
def accounttodict(account):
    return {
        "name": account.mname,
        "account": account.maccount,
        "salt": account.salt,
        "password_hash": account.password_hash,
        "balance": account.balance,
        "history": account.mhistory,
        "email": account.memail,
        "phone": account.mphonenumber
    }


# DICTIONARY TO OBJECT
def dicttoaccount(data):
    account = Bankaccount(
        data["name"],
        data["account"],
        "",
        data.get("email", ""),
        data.get("phone", ""),
        salt=data["salt"],
        stored_hash=data["password_hash"]
    )

    account.balance = data["balance"]
    account.mhistory = data["history"]

    return account


# LOAD DATA
def load():
    if not os.path.exists(DATA_FILE):
        return

    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Invalid account data")

        loaded_accounts = [
            dicttoaccount(item) for item in data
        ]

        accounts.extend(loaded_accounts)

    except (json.JSONDecodeError, KeyError,
            TypeError, ValueError, OSError) as error:

        messagebox.showerror(
            "Loading Error",
            f"Unable to load data:\n{error}"
        )


# SAVE DATA
def save_data():
    data = [
        accounttodict(account)
        for account in accounts
    ]

    try:
        with open(DATA_FILE, "w") as file:
            json.dump(data, file, indent=4)

        return True

    except OSError as error:
        messagebox.showerror(
            "Saving Error",
            str(error)
        )
        return False


# MAIN WINDOW
root = tk.Tk()
root.title("BANK ACCOUNT MANAGEMENT SYSTEM")
root.geometry("350x550")
root.resizable(False, False)
root.configure(bg="#6f72b9")

load()


# FRAME MANAGEMENT
def switch_frame(frame):
    frame.tkraise()


frames = {}

for name in ("main", "create", "login", "account"):
    frames[name] = tk.Frame(
        root,
        bg="#6f72b9"
    )
    frames[name].place(
        relwidth=1,
        relheight=1
    )

main_menu = frames["main"]
create_frame = frames["create"]
login_frame = frames["login"]
account_menu = frames["account"]


# COMMON LABEL AND BUTTON FUNCTIONS
def create_label(parent, text):
    label = tk.Label(
        parent,
        text=text,
        bg="#6f72b9",
        fg="white",
        font=("Arial", 11)
    )
    label.pack(pady=5)
    return label


def create_button(parent, text, command):
    button = tk.Button(
        parent,
        text=text,
        width=20,
        command=command,
        font=("Arial", 10, "bold"),
        bg="white",
        fg="#333333"
    )
    button.pack(pady=7)
    return button

    # MAIN MENU
create_label(main_menu, "BANK ACCOUNT SYSTEM")

create_button(
    main_menu,
    "Create Account",
    lambda: switch_frame(create_frame)
)

create_button(
    main_menu,
    "Login",
    lambda: switch_frame(login_frame)
)


# CREATE ACCOUNT FUNCTION
def create_account():

    name = name_textbox.get().strip()
    accountnumber = accountnumber_textbox.get().strip()
    password = password_textbox.get()
    email = email_textbox.get().strip()
    phone = phonenumber_textbox.get().strip()

    if not name or not accountnumber or not password:
        messagebox.showwarning(
            "Missing Data",
            "Please fill all required fields!"
        )
        return

    if not accountnumber.isdigit():
        messagebox.showerror(
            "Error",
            "Account number must be numeric!"
        )
        return

    if len(password) < 8:
        messagebox.showerror(
            "Error",
            "Password must contain at least 8 characters!"
        )
        return

    if any(acc.maccount == accountnumber for acc in accounts):
        messagebox.showerror(
            "Error",
            "Account number already exists!"
        )
        return

    new_account = Bankaccount(
        name,
        accountnumber,
        password,
        email,
        phone
    )

    accounts.append(new_account)

    if not save_data():
        accounts.remove(new_account)
        return

    messagebox.showinfo(
        "Success",
        f"Welcome {name}!\n"
        f"Account created successfully!\n"
        f"Account Number: {accountnumber}"
    )

    for entry in (
        name_textbox,
        accountnumber_textbox,
        password_textbox,
        email_textbox,
        phonenumber_textbox
    ):
        entry.delete(0, tk.END)

    switch_frame(main_menu)


# CREATE ACCOUNT SCREEN
create_label(create_frame, "CREATE ACCOUNT")

create_label(create_frame, "Name")
name_textbox = tk.Entry(create_frame)
name_textbox.pack()

create_label(create_frame, "Account Number")
accountnumber_textbox = tk.Entry(create_frame)
accountnumber_textbox.pack()

create_label(create_frame, "Password")
password_textbox = tk.Entry(create_frame, show="*")
password_textbox.pack()

create_label(create_frame, "Email")
email_textbox = tk.Entry(create_frame)
email_textbox.pack()

create_label(create_frame, "Phone Number")
phonenumber_textbox = tk.Entry(create_frame)
phonenumber_textbox.pack()

create_button(
    create_frame,
    "CREATE",
    create_account
)

create_button(
    create_frame,
    "BACK",
    lambda: switch_frame(main_menu)
)


# LOGIN FUNCTION
def login_account():

    global current_account

    accountnumber = laccountnumber_textbox.get().strip()
    password = lpassword_textbox.get()

    if not accountnumber or not password:
        messagebox.showerror(
            "Error",
            "Please fill all fields!"
        )
        return

    if not accountnumber.isdigit():
        messagebox.showerror(
            "Error",
            "Account number must be numeric!"
        )
        return

    for account in accounts:

        if (
            account.maccount == accountnumber
            and account.check_password(password)
        ):

            current_account = account

            messagebox.showinfo(
                "Login Successful",
                f"Welcome {account.mname}!"
            )

            laccountnumber_textbox.delete(0, tk.END)
            lpassword_textbox.delete(0, tk.END)

            switch_frame(account_menu)
            return

    messagebox.showerror(
        "Login Failed",
        "Invalid account number or password!"
    )


# LOGIN SCREEN
create_label(login_frame, "LOGIN ACCOUNT")

create_label(login_frame, "Account Number")
laccountnumber_textbox = tk.Entry(login_frame)
laccountnumber_textbox.pack()

create_label(login_frame, "Password")
lpassword_textbox = tk.Entry(login_frame, show="*")
lpassword_textbox.pack()

create_button(
    login_frame,
    "LOGIN",
    login_account
)

create_button(
    login_frame,
    "BACK",
    lambda: switch_frame(main_menu)
)


# CHECK LOGIN STATUS
def check_login():

    if current_account is None:
        messagebox.showerror(
            "Error",
            "Please login first!"
        )
        return False

    return True

# ACCOUNT INFORMATION
def show_account_info():

    if not check_login():
        return

    messagebox.showinfo(
        "Account Information",
        current_account.info()
    )


# DEPOSIT
def deposit():

    if not check_login():
        return

    amount = simpledialog.askinteger(
        "Deposit",
        "Enter deposit amount:",
        minvalue=1,
        parent=root
    )

    if amount is None:
        return

    result = current_account.deposit(amount)

    if save_data():
        messagebox.showinfo(
            "Deposit Successful",
            result
        )


# WITHDRAW
def withdraw():

    if not check_login():
        return

    amount = simpledialog.askinteger(
        "Withdraw",
        "Enter withdrawal amount:",
        minvalue=1,
        parent=root
    )

    if amount is None:
        return

    result = current_account.withdraw(amount)

    if result in (
        "Insufficient balance!",
        "Invalid withdrawal amount!"
    ):
        messagebox.showerror("Error", result)
        return

    if save_data():
        messagebox.showinfo(
            "Withdrawal Successful",
            result
        )


# TRANSFER
def transfer():

    if not check_login():
        return

    recipient_number = simpledialog.askstring(
        "Transfer",
        "Enter recipient account number:",
        parent=root
    )

    if recipient_number is None:
        return

    recipient_number = recipient_number.strip()

    if not recipient_number.isdigit():
        messagebox.showerror(
            "Error",
            "Account number must be numeric!"
        )
        return

    recipient = None

    for account in accounts:
        if account.maccount == recipient_number:
            recipient = account
            break

    if recipient is None:
        messagebox.showerror(
            "Error",
            "Recipient account not found!"
        )
        return

    if recipient == current_account:
        messagebox.showerror(
            "Error",
            "You cannot transfer to your own account!"
        )
        return

    amount = simpledialog.askinteger(
        "Transfer",
        "Enter transfer amount:",
        minvalue=1,
        parent=root
    )

    if amount is None:
        return

    if amount > current_account.balance:
        messagebox.showerror(
            "Error",
            "Insufficient balance!"
        )
        return

    # Deduct money from sender
    current_account.debit(amount)

    # Add money to recipient
    recipient.credit(amount)

    # Record transaction history
    current_account.addlog(
        "Transfer",
        f"To {recipient.maccount}",
        amount
    )

    recipient.addlog(
        "Transfer",
        f"From {current_account.maccount}",
        amount
    )

    if save_data():
        messagebox.showinfo(
            "Transfer Successful",
            f"Transferred: ₹{amount}\n\n"
            f"Your balance: ₹{current_account.balance}\n"
            f"Recipient balance: ₹{recipient.balance}"
        )


# TRANSACTION HISTORY
def history():

    if not check_login():
        return

    if not current_account.mhistory:
        messagebox.showinfo(
            "History",
            "No transactions yet!"
        )
        return

    history_text = ""

    for transaction in current_account.mhistory:

        history_text += (
            f"ID: {transaction[0]}\n"
            f"Operation: {transaction[1]}\n"
            f"Description: {transaction[2]}\n"
            f"Amount: ₹{transaction[3]}\n"
            f"Date: {transaction[4]}\n"
            f"--------------------------\n"
        )

    messagebox.showinfo(
        "Transaction History",
        history_text
    )


# CHECK BALANCE
def checkbalance():

    if not check_login():
        return

    messagebox.showinfo(
        "Balance",
        current_account.checkbalance()
    )


# LOGOUT
def logout():

    global current_account

    if current_account is None:
        return

    if not save_data():
        return

    current_account = None

    messagebox.showinfo(
        "Logout",
        "You have successfully logged out!"
    )

    switch_frame(main_menu)


# ACCOUNT MENU
create_label(account_menu, "ACCOUNT MENU")

create_button(
    account_menu,
    "Account Information",
    show_account_info
)

create_button(
    account_menu,
    "Deposit",
    deposit
)

create_button(
    account_menu,
    "Withdraw",
    withdraw
)

create_button(
    account_menu,
    "Transfer",
    transfer
)

create_button(
    account_menu,
    "Transaction History",
    history
)

create_button(
    account_menu,
    "Check Balance",
    checkbalance
)

create_button(
    account_menu,
    "Logout",
    logout
)


# EXIT APPLICATION
def on_close():

    if save_data():
        root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    on_close
)


# START APPLICATION
switch_frame(main_menu)

root.mainloop()