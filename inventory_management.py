# inventory_management.py

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox
import sqlite3
from PyQt5.QtCore import QStringListModel ,QDate
from PyQt5.QtWidgets import QCompleter,QDateEdit
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtWidgets import QDialog, QTableWidget, QVBoxLayout, QTableWidgetItem
from PyQt5.QtGui import QBrush, QColor
import uuid
import hashlib
from PyQt5.QtGui import QFont ,QIcon
import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QWidget, QComboBox, QFileDialog
import csv



class ViewTransactionsDialog(QDialog):
    def __init__(self, cursor, parent=None):
        super().__init__(parent)

        self.setWindowTitle("View Transactions")
        self.setGeometry(400, 400, 970, 400)

        self.layout = QVBoxLayout()

        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(7)
        self.transaction_table.setHorizontalHeaderLabels(["ID","Product ID", "Transaction Type", "Quantity","Price","Total","Date"])

       

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFixedSize(70, 30)
        self.delete_button.setIcon(QIcon("delete_icon.png"))
        self.date_range_start = QDateEdit()
        self.date_range_end = QDateEdit()
        self.date_range_start.setCalendarPopup(True)
        self.date_range_end.setCalendarPopup(True)

        today = QDate.currentDate()
        self.date_range_start.setDate(today)
        self.date_range_end.setDate(today)

        # Connect date edit widgets' signals to the slot for fetching transactions
        self.date_range_start.dateChanged.connect(lambda: self.fetch_transactions(cursor))
        self.date_range_end.dateChanged.connect(lambda: self.fetch_transactions(cursor))

        
        self.delete_button.clicked.connect(lambda: self.delete_selected_row(cursor))
        
        # Add widgets to layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.date_range_start)
        button_layout.addWidget(self.date_range_end)

        self.layout.addLayout(button_layout)

        self.load_transactions(cursor)
        self.layout.addWidget(self.transaction_table)
        self.setLayout(self.layout)

         # Apply style sheet for enhanced appearance
        self.setStyleSheet("""
            QTableWidget {
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 0.9em;
                font-family: sans-serif;
                min-width: 400px;
                
            }

            QTableWidget QHeaderView::section {
                background-color: #009879;
                color: #ffffff;
                text-align: left;
            }

            QTableWidget::item {
                padding: 12px 15px;
            }

            QTableWidget::item:selected {
                color: #000000;
                font-weight: bold;
            }             
                    
            QTableWidget:item {
                border-bottom: 1px solid #dddddd; /* Border for each row */
            }

            QTableWidget:item:nth-of-type(even) {
                background-color: #f3f3f3; /* Zebra striping for even rows */
            }

            QTableWidget:item:last-of-type {
                border-bottom: 2px solid #009879; /* Distinct border for the last row */
            }
        """)

    def load_transactions(self, cursor):
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()

        self.transaction_table.setRowCount(len(transactions))

        for row, transaction in enumerate(transactions):
            for col, value in enumerate(transaction):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                

                if transaction[2] == "Buy":  # Assuming column 2 is the "Transaction Type" column
                    item.setForeground(QBrush(QColor(255, 0, 0)))  # Red for buy
                elif transaction[2] == "Sell":
                    item.setForeground(QBrush(QColor(0, 255, 0)))  # Green for sell
                
                self.transaction_table.setItem(row, col, item)

    def delete_selected_row(self,cursor):
        selected_row = self.transaction_table.currentRow()

        if selected_row >= 0:

        # Get the transaction ID from the selected row's item
            transaction_id_item = self.transaction_table.item(selected_row, 0)  # Assuming the ID is in the first column
            transaction_id = transaction_id_item.text()

        # Remove the row from the table
            self.transaction_table.removeRow(selected_row)

        
            cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
            cursor.connection.commit()

        # Reload transactions after deletion
            self.load_transactions(cursor)
            self.parent().update_total_sales_and_purchases()
    
    
    def fetch_transactions(self,cursor):
        # Get start and end dates from date range widgets
        start_date = self.date_range_start.date().toString("yyyy-MM-dd")
        end_date = self.date_range_end.date().toString("yyyy-MM-dd")

        # Clear existing table contents
        self.transaction_table.clearContents()

        # Fetch transactions from the database for the selected date range
        query = """
            SELECT * FROM transactions
            WHERE timestamp BETWEEN ? AND ?
        """
        cursor.execute(query, (start_date, end_date))
        transactions = cursor.fetchall()

        # Update the table with the fetched data
        self.transaction_table.setRowCount(len(transactions))
        for row, transaction in enumerate(transactions):
            for col, value in enumerate(transaction):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                # Set font color based on transaction type
                if transaction[2] == "Buy":
                    item.setForeground(QBrush(QColor(255, 0, 0)))  # Red for buy
                elif transaction[2] == "Sell":
                    item.setForeground(QBrush(QColor(0, 255, 0)))  # Green for sell
                
                self.transaction_table.setItem(row, col, item)

class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add New Product")
        self.setGeometry(400, 400, 600, 400)

        # Apply a modern and clean style
        self.setStyleSheet("""
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        """)

        self.layout = QVBoxLayout()

        # Create labels with a bold font
        self.name_label = QLabel("Product Name:")
        self.name_label.setStyleSheet("font-weight: bold;")
        self.model_label = QLabel("Model No:")
        self.model_label.setStyleSheet("font-weight: bold;")
        self.part_label = QLabel("Part name:")
        self.part_label.setStyleSheet("font-weight: bold;")
        self.quantity_label = QLabel("Initial Quantity:")
        self.quantity_label.setStyleSheet("font-weight: bold;")
        self.price_label = QLabel("Unit Price:")
        self.price_label.setStyleSheet("font-weight: bold;")

        # Create line edits with a rounded border
        self.name_entry = QLineEdit()
        self.name_entry.setStyleSheet("border: 1px solid #ccc; border-radius: 5px;")
        self.model_entry = QLineEdit()
        self.model_entry.setStyleSheet("border: 1px solid #ccc; border-radius: 5px;")
        self.part_entry = QLineEdit()
        self.part_entry.setStyleSheet("border: 1px solid #ccc; border-radius: 5px;")
        self.quantity_entry = QLineEdit()
        self.quantity_entry.setStyleSheet("border: 1px solid #ccc; border-radius: 5px;")
        self.price_entry = QLineEdit()
        self.price_entry.setStyleSheet("border: 1px solid #ccc; border-radius: 5px;")

        # Create a rounded button with a gradient background
        self.add_button = QPushButton("Add Product")
        self.add_button.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop: 0 #4CAF50, stop: 1 #45a049);
            color: white;
            border: 1px solid #4CAF50;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 14px;
        """)
        self.add_button.clicked.connect(self.add_product)

        # Add widgets to the layout
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_entry)
        self.layout.addWidget(self.model_label)
        self.layout.addWidget(self.model_entry)
        self.layout.addWidget(self.part_label)
        self.layout.addWidget(self.part_entry)
        self.layout.addWidget(self.quantity_label)
        self.layout.addWidget(self.quantity_entry)
        self.layout.addWidget(self.price_label)
        self.layout.addWidget(self.price_entry)
        self.layout.addWidget(self.add_button)

        # Set the layout for the window
        self.setLayout(self.layout)

    def add_product(self):
        name = self.name_entry.text()
        model_no = self.model_entry.text()
        part_name = self.part_entry.text()
        quantity = self.quantity_entry.text()
        price = self.price_entry.text()

        if not name or not model_no or not part_name or not quantity.isdigit() or not price.isdigit():
            QMessageBox.warning(self, "Error", "Please enter valid product information.")
            return

        quantity = int(quantity)
        price = int(price)
        self.parent().cursor.execute("SELECT * FROM products WHERE name=? AND model_no=? AND part_name=?", (name, model_no, part_name))
        existing_product = self.parent().cursor.fetchone()

        if existing_product:
            QMessageBox.warning(self, "Error", "Product already exists.")
            return
        
        product_details = f"{name}{model_no}{part_name}"
        product_id = hashlib.sha256(product_details.encode()).hexdigest()[:8]  # Truncate to 8 characters

        self.parent().cursor.execute("INSERT INTO products (id, name, model_no, part_name, quantity,price) VALUES (?, ?, ?, ?, ?,?)",
                            (product_id, name, model_no, part_name, quantity,price))
        self.parent().connection.commit()
        self.parent().load_inventory()

        self.name_entry.clear()
        self.model_entry.clear()
        self.part_entry.clear()
        self.quantity_entry.clear()
        self.accept()  

class InventoryManagementApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Inventory Management")
        self.setGeometry(100, 100, 1500, 700)

        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #333;
                font-weight: bold;
            }

            QLineEdit, QComboBox {
                font-size: 12px;
                padding: 5px;
                margin: 5px;
                border: 1px solid #ccc;
                border-radius: 5px;
            } 
        """)
        

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.product_label = QLabel("Product Name:")
        self.product_entry = QLineEdit()
        self.model_label = QLabel("Model No:")
        self.model_entry = QComboBox()
        self.part_label = QLabel("Part name:")
        self.part_entry = QComboBox()
        self.quantity_label = QLabel("Quantity:")
        self.quantity_entry = QLineEdit()
        self.price_label = QLabel("Price:")
        self.price_entry = QLineEdit() 
        self.buy_button = QPushButton("Buy", self)
        self.sell_button = QPushButton("Sell", self)
        # Create QLabel widgets for total sales and total purchases
        self.total_sales_label = QLabel("Total Sales: ", self)
        self.total_purchases_label = QLabel("Total Purchases: ", self)
        self.total_sales_label.setObjectName("totalSalesLabel")
        self.total_purchases_label.setObjectName("totalPurchasesLabel")

        self.total_sales_label.setStyleSheet(
            "QLabel#totalSalesLabel {"
            "   font-size: 18px;"
            "   font-weight: bold;"
            "   color: #4CAF50;"  # Green color for sales
            "}")

        self.total_purchases_label.setStyleSheet(
            "QLabel#totalPurchasesLabel{"
            "   font-size: 18px;"
            "   font-weight: bold;"
            "   color: #008CBA;"  # Blue color for purchases
             "}")

        self.export_sales_button = QPushButton("Export Sales", self)
        self.export_purchases_button = QPushButton("Export Purchases", self)

        self.export_sales_button.clicked.connect(self.export_sales_transactions)
        self.export_purchases_button.clicked.connect(self.export_purchases_transactions)

        self.buy_button.clicked.connect(self.record_transaction)
        self.sell_button.clicked.connect(self.record_transaction)

          # Set button sizes
        #self.export_sales_button.setFixedSize(200, 40)
        #self.export_purchases_button.setFixedSize(200, 40)
        self.buy_button.setFixedSize(120, 30)
        self.sell_button.setFixedSize(120, 30)

        # Set button colors using style sheets
        self.export_sales_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.export_purchases_button.setStyleSheet("background-color: #008CBA; color: white;")
        self.buy_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.sell_button.setStyleSheet("background-color: #008CBA; color: white;")


        
        # Set font for the total sales and total purchases labels
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.total_sales_label.setFont(font)
        self.total_purchases_label.setFont(font)

        buttonfont = QFont()
        buttonfont.setPointSize(12)
        buttonfont.setBold(True)
        #buttonfont.setItalic(True)
        self.buy_button.setFont(buttonfont)
        self.sell_button.setFont(buttonfont)
        self.export_purchases_button.setFont(buttonfont)
        self.export_sales_button.setFont(buttonfont)


        
        self.form_layout = QHBoxLayout()
        self.form_layout.addWidget(self.product_label)
        self.form_layout.addWidget(self.product_entry)
        self.form_layout.addWidget(self.model_label)
        self.form_layout.addWidget(self.model_entry)
        self.form_layout.addWidget(self.part_label)
        self.form_layout.addWidget(self.part_entry)
        self.form_layout.addWidget(self.quantity_label)
        self.form_layout.addWidget(self.quantity_entry)
        self.form_layout.addWidget(self.price_label)  # New label for price
        self.form_layout.addWidget(self.price_entry)
        self.form_layout.addWidget(self.buy_button)
        self.form_layout.addWidget(self.sell_button)
        
         

        # Add total sales and total purchases labels to the layout
        self.main_layout.addWidget(self.total_sales_label)
        
        self.main_layout.addWidget(self.total_purchases_label)
        

     
        self.table_label = QLabel("Inventory")
        self.table_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)  # Added two columns for delete and update buttons
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Product Name","Model No" , "Part Name" ,"Quantity","Price" , "Delete", "Update"])
        
        
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.table_label)
        self.main_layout.addWidget(self.inventory_table)

        self.create_database()
        self.load_inventory()
        self.update_total_sales_and_purchases()


        # Create a QStringListModel to store product suggestions
        self.suggestions_model = QStringListModel()
        self.completer = QCompleter(self.suggestions_model)
        self.product_entry.setCompleter(self.completer)

        # Connect the textChanged signal to update suggestions
        self.product_entry.textChanged.connect(self.update_product_suggestions)
         # Connect signals to slots
        self.product_entry.textChanged.connect(self.update_model_numbers)
        self.model_entry.currentIndexChanged.connect(self.update_part_names)
        self.part_entry.currentIndexChanged.connect(self.update_price)

        # Add a button to open the Add Product window
        self.add_product_button = QPushButton("Add New Product")
        self.add_product_button.clicked.connect(self.show_add_product_window)

        # Add a button to open the View Transactions window
        self.view_transactions_button = QPushButton("View Transactions")
        self.view_transactions_button.clicked.connect(self.show_view_transactions_window)

        #self.add_product_button.setFixedSize(250, 45)
        #self.view_transactions_button.setFixedSize(250, 45)

        self.add_product_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.view_transactions_button.setStyleSheet("background-color: #008CBA; color: white;")

        #self.main_layout.addWidget(self.add_product_button)
        #self.main_layout.addWidget(self.view_transactions_button)
        self.add_product_button.setFont(buttonfont)
        self.view_transactions_button.setFont(buttonfont)

         # Add buttons to a horizontal layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_product_button)
        button_layout.addWidget(self.view_transactions_button)
        button_layout.addWidget(self.export_sales_button)
        button_layout.addWidget(self.export_purchases_button)
          


        # Add the horizontal layout to the main layout
        self.main_layout.addLayout(button_layout)
        

    def create_database(self):
        self.connection = sqlite3.connect('inventory.db')
        self.cursor = self.connection.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                model_no TEXT,
                part_name TEXT,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        self.connection.commit()

    def load_inventory(self):
        self.inventory_table.setRowCount(0)

        self.cursor.execute("SELECT * FROM products")
        products = self.cursor.fetchall()

        buttonfont2 = QFont()
        buttonfont2.setPointSize(8)
        buttonfont2.setBold(True)
        
        for row, product in enumerate(products):
            self.inventory_table.insertRow(row)

            for col, value in enumerate(product):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable) 
                self.inventory_table.setItem(row, col, item)
    
            # Add buttons for delete and update in each row
            delete_button = QPushButton("Delete")
            delete_button.setFixedSize(70, 30)
            delete_button.setIcon(QIcon("delete_icon.png"))
            delete_button.setFont(buttonfont2)
            # Replace with the actual path to your sales icon
        
            delete_button.clicked.connect(lambda _, row=row, product_id=product[0]: self.delete_product(row, product_id))
            self.inventory_table.setCellWidget(row, col + 1, delete_button)

            update_button = QPushButton("Edit")
            update_button.setFixedSize(70,30)
            update_button.setIcon(QIcon("edit_icon.png"))
            update_button.setFont(buttonfont2)
            
            update_button.clicked.connect(lambda _, row=row, product_id=product[0]: self.show_update_product_window(row, product_id))
            self.inventory_table.setCellWidget(row, col + 2, update_button)

    def update_product_suggestions(self):
        partial_name = self.product_entry.text()
        self.cursor.execute("SELECT DISTINCT name FROM products WHERE name LIKE ?", (f"%{partial_name}%",))
        suggestions = [suggestion[0] for suggestion in self.cursor.fetchall()]

        # Set the suggestions to the QStringListModel
        self.suggestions_model.setStringList(suggestions)
    
    def show_add_product_window(self):
        add_product_dialog = AddProductDialog(self)
        add_product_dialog.exec_()

    def record_transaction(self):
        product_name = self.product_entry.text()
        model_no = self.model_entry.currentText()
        part_name = self.part_entry.currentText()
        quantity = self.quantity_entry.text()
        price_str = self.price_entry.text()
        price_str = price_str.replace('.', '')
       

        if not product_name or not model_no or not part_name or not quantity.isdigit() or not price_str.isdigit():
            QMessageBox.warning(self, "Error", "Please enter valid product information.")
            return

        quantity = int(quantity)
        price = float(price_str)

        self.cursor.execute("SELECT * FROM products WHERE name=? AND model_no=? AND part_name=?", (product_name,model_no,part_name))
        existing_product = self.cursor.fetchone()

        if not existing_product:
            QMessageBox.warning(self, "Error", f"Product '{product_name}' does not exist in the inventory.")
            return

        product_id = existing_product[0]
        current_quantity = existing_product[4]
        

        # Determine the transaction type based on which button was clicked
        transaction_type = None

        if self.sender() == self.buy_button:
            transaction_type = "Buy"
        elif self.sender() == self.sell_button:
            transaction_type = "Sell"

        if transaction_type is None:
            QMessageBox.warning(self, "Error", "Please select a transaction type.")
            return

        # Handle Buy or Sell based on the button clicked
        if transaction_type == "Sell" and quantity > current_quantity:
            QMessageBox.warning(self, "Error", "Not enough quantity available for sale.")
            return

        new_quantity = current_quantity - quantity if transaction_type == "Sell" else current_quantity + quantity
        
        transaction_id = str(uuid.uuid4())

            # Calculate total price for the transaction
        total_price = quantity * price

        self.cursor.execute("UPDATE products SET quantity=? WHERE id=?", (new_quantity, product_id))
        self.cursor.execute("INSERT INTO transactions (id,product_id, transaction_type, quantity,price,total_amount) VALUES (?,?, ?, ?,?,?)",
                            (transaction_id,product_id, transaction_type, quantity,price,total_price))

        self.connection.commit()
        self.load_inventory()
        self.product_entry.clear()
        self.model_entry.clear()
        self.part_entry.clear()
        self.update_total_sales_and_purchases()
        self.quantity_entry.clear()
        self.price_entry.clear()
        QMessageBox.information(self, "Success", f"Transaction recorded successfully: {transaction_type} {quantity} units.")

    def show_view_transactions_window(self):
        view_transactions_dialog = ViewTransactionsDialog(self.cursor, self)
        view_transactions_dialog.exec_()

    def delete_product(self, row, product_id):
        reply = QMessageBox.question(self, 'Delete Product', 'Are you sure you want to delete this product?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
            self.connection.commit()
            self.load_inventory()

    def show_update_product_window(self, row, product_id):
        update_product_dialog = UpdateProductDialog(self.cursor, product_id, self)
        if update_product_dialog.exec_() == QDialog.Accepted:
            self.load_inventory()

    def update_total_sales_and_purchases(self):
        # Get today's date
        today = datetime.date.today()

        # Calculate total sales and total purchases for the day
        self.cursor.execute("SELECT SUM(quantity * price) FROM transactions WHERE transaction_type='Sell' AND DATE(timestamp)=?", (today,))
        total_sales_result = self.cursor.fetchone()

        self.cursor.execute("SELECT SUM(quantity * price) FROM transactions WHERE transaction_type='Buy' AND DATE(timestamp)=?", (today,))
        total_purchases_result = self.cursor.fetchone()

        total_sales = total_sales_result[0] if total_sales_result[0] else 0
        total_purchases = total_purchases_result[0] if total_purchases_result[0] else 0

        # Update the total sales and total purchases labels
        self.total_sales_label.setText(f"Total Sales: ${total_sales:.2f}")
        self.total_purchases_label.setText(f"Total Purchases: ${total_purchases:.2f}")
    
    def update_model_numbers(self):
        # Fetch model numbers associated with the selected product name
        selected_product = self.product_entry.text()
        self.cursor.execute("SELECT DISTINCT model_no FROM products WHERE name=?", (selected_product,))
        models = self.cursor.fetchall()

        # Clear existing items and populate the combo box with model numbers
        self.model_entry.clear()
        for model in models:
            self.model_entry.addItem(model[0])

    def update_part_names(self):
        # Fetch part names associated with the selected product name and model number
        selected_product = self.product_entry.text()
        selected_model = self.model_entry.currentText()
        self.cursor.execute("SELECT DISTINCT part_name FROM products WHERE name=? AND model_no=?", (selected_product, selected_model))
        parts = self.cursor.fetchall()

        # Clear existing items and populate the combo box with part names
        self.part_entry.clear()
        for part in parts:
            self.part_entry.addItem(part[0])

    def export_sales_transactions(self):
        # Fetch and export sales transactions of the day to a CSV file
        today = datetime.date.today().strftime('%Y-%m-%d')
        filename, _ = QFileDialog.getSaveFileName(self, "Save Sales Transactions CSV", f"sales_transactions_{today}.csv", "CSV Files (*.csv)")

        if filename:
            with open(filename, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(["Transaction ID", "Product Name", "Model Number", "Part Name", "Quantity", "Price", "Total Price", "Timestamp"])

                query = """
                SELECT t.id, p.name, p.model_no, p.part_name, t.quantity, t.price, t.total_amount, t.timestamp
                FROM transactions t
                JOIN products p ON t.product_id = p.id
                WHERE t.transaction_type='Sell' AND date(t.timestamp) = ?
                """
                self.cursor.execute(query, (today,))
                sales_data = self.cursor.fetchall()

                for row in sales_data:
                    csvwriter.writerow(row)

    def export_purchases_transactions(self):
        # Fetch and export purchases transactions of the day to a CSV file
        today = datetime.date.today().strftime('%Y-%m-%d')
        filename, _ = QFileDialog.getSaveFileName(self, "Save Purchases Transactions CSV", f"purchases_transactions_{today}.csv", "CSV Files (*.csv)")

        if filename:
            with open(filename, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(["Transaction ID", "Product Name", "Model Number", "Part Name", "Quantity", "Price", "Total Price", "Timestamp"])

                query = """
                SELECT t.id, p.name, p.model_no, p.part_name, t.quantity, t.price, t.total_amount, t.timestamp
                FROM transactions t
                JOIN products p ON t.product_id = p.id
                WHERE t.transaction_type='Buy' AND date(t.timestamp) = ?
                """
                self.cursor.execute(query, (today,))
                purchases_data = self.cursor.fetchall()

                for row in purchases_data:
                    csvwriter.writerow(row)

    def update_price(self):
        product_name = self.product_entry.text()
        model_no = self.model_entry.currentText()
        part_name = self.part_entry.currentText()

        # Implement logic to fetch the price based on product name, model no, and part name
        # For example, you might have a database query to fetch the price from the database
        # Replace the following line with your logic to fetch the price
        self.cursor.execute("SELECT price FROM products WHERE name=? AND model_no=? AND part_name=?", ( product_name, model_no,part_name))
        price = self.cursor.fetchone()

        if price:
                
                price = price[0]  # Assuming the 'price' column is the first column in the query result
        else:
                price =  0.0 
        # Update the price entry field
        self.price_entry.setText(str(price))

class UpdateProductDialog(QDialog):
    def __init__(self, cursor, product_id, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Update Product")
        self.setGeometry(200, 200, 400, 200)

        self.product_id = product_id
        self.cursor = cursor

        self.layout = QVBoxLayout()

        self.name_label = QLabel("Product Name:")
        self.name_entry = QLineEdit()
        self.quantity_label = QLabel("Updated Quantity:")
        self.quantity_entry = QLineEdit()

        self.update_button = QPushButton("Update Product")
        self.update_button.clicked.connect(self.update_product)

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_entry)
        self.layout.addWidget(self.quantity_label)
        self.layout.addWidget(self.quantity_entry)
        self.layout.addWidget(self.update_button)

        self.load_product_data()

        self.setLayout(self.layout)

    def load_product_data(self):
        self.cursor.execute("SELECT * FROM products WHERE id=?", (self.product_id,))
        product = self.cursor.fetchone()

        if product:
            self.name_entry.setText(product[1])

    def update_product(self):
        name = self.name_entry.text()
        quantity = self.quantity_entry.text()

        if not name or not quantity.isdigit():
            QMessageBox.warning(self, "Error", "Please enter valid product information.")
            return

        quantity = int(quantity)

        self.cursor.execute("UPDATE products SET name=?, quantity=? WHERE id=?", (name, quantity, self.product_id))
        self.parent().connection.commit()
        self.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InventoryManagementApp()
    window.show()
    sys.exit(app.exec_())
