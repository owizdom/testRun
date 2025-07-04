import mysql.connector
import getpass
import sys
import re
import csv
from datetime import datetime
import logging
import subprocess
import os
import stat
import venv
import platform

# Configure logging to track application events and errors
logging.basicConfig(
    filename='edu_enroll.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MySQL credentials (password will be determined dynamically)
MYSQL_USER = "root"
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')  # Try environment variable or empty string
MYSQL_HOST = "localhost"
MYSQL_DATABASE = "student_db"

def setup_environment():
    """
    Sets up the virtual environment, installs dependencies, and ensures MySQL is running.
    Creates virtual environment, installs mysql-connector-python, and starts MySQL server if needed.
    """
    print("[+] Setting up environment...")
    logging.info("Starting environment setup")

    # Check and create virtual environment
    venv_dir = os.path.join(os.getcwd(), "venv")
    if not os.path.exists(venv_dir):
        print("[+] Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
        logging.info("Virtual environment created")
    else:
        print("[+] Virtual environment already exists")
        logging.info("Virtual environment already exists")

    # Determine pip path based on platform
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        activate_script = os.path.join(venv_dir, "Scripts", "activate.bat")
    else:  # macOS or Linux
        pip_path = os.path.join(venv_dir, "bin", "pip")
        activate_script = os.path.join(venv_dir, "bin", "activate")

    # Ensure activation script is executable (Linux/macOS)
    if platform.system() != "Windows" and os.path.exists(activate_script):
        os.chmod(activate_script, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)
        logging.info("Virtual environment activation script set as executable")
    elif not os.path.exists(activate_script):
        print("[+] Error: Virtual environment activation script not found")
        logging.error("Virtual environment activation script not found")
        sys.exit(1)

    # Ensure pip is upgraded
    try:
        subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
        print("[+] Upgraded pip in virtual environment")
        logging.info("Upgraded pip in virtual environment")
    except subprocess.CalledProcessError as e:
        print(f"[+] Warning: Failed to upgrade pip: {e}")
        logging.warning(f"Failed to upgrade pip: {e}")

    # Install mysql-connector-python if not already installed
    try:
        subprocess.check_call([pip_path, "show", "mysql-connector-python"])
        print("[+] mysql-connector-python already installed")
        logging.info("mysql-connector-python already installed")
    except subprocess.CalledProcessError:
        print("[+] Installing mysql-connector-python...")
        try:
            subprocess.check_call([pip_path, "install", "mysql-connector-python"])
            print("[+] Installed mysql-connector-python")
            logging.info("mysql-connector-python installed")
        except subprocess.CalledProcessError as e:
            print(f"[+] Error installing mysql-connector-python: {e}")
            logging.error(f"Error installing mysql-connector-python: {e}")
            sys.exit(1)

    # Check if MySQL is installed
    try:
        subprocess.check_call(["mysql", "--version"])
        print("[+] MySQL is installed")
        logging.info("MySQL is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[+] MySQL not found. Please install MySQL manually:")
        if platform.system() == "Darwin":
            print("[+] On macOS, run: brew install mysql")
        elif platform.system() == "Linux":
            print("[+] On Linux, run: sudo apt update && sudo apt install -y mysql-server")
        else:
            print("[+] On Windows, download and install MySQL from https://dev.mysql.com/downloads/")
        logging.error("MySQL not found, manual installation required")
        sys.exit(1)

    # Start MySQL server
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.check_call(["brew", "services", "start", "mysql"])
        elif platform.system() == "Linux":
            subprocess.check_call(["service", "mysql", "start"])
        else:  # Windows
            print("[+] On Windows, ensure MySQL is running (e.g., via Services or mysqld)")
        print("[+] MySQL server started")
        logging.info("MySQL server started")
    except subprocess.CalledProcessError as e:
        print(f"[+] Warning: Could not start MySQL automatically: {e}")
        print("[+] MySQL may already be running or requires manual start")
        logging.warning(f"Could not start MySQL: {e}")

    # Check if student_db exists, create if not
    global MYSQL_PASSWORD
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS student_db")
        print("[+] Database 'student_db' ensured")
        logging.info("Database 'student_db' ensured")
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("[+] Default MySQL password failed. Please enter the MySQL root password:")
            MYSQL_PASSWORD = getpass.getpass("[+] MySQL root password: ")
            try:
                conn = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD
                )
                cursor = conn.cursor()
                cursor.execute("CREATE DATABASE IF NOT EXISTS student_db")
                print("[+] Database 'student_db' ensured")
                logging.info("Database 'student_db' ensured")
                cursor.close()
                conn.close()
            except mysql.connector.Error as err:
                print(f"[+] Error: Failed to create database: {err}")
                logging.error(f"Failed to create database: {err}")
                sys.exit(1)
        else:
            print(f"[+] Error: Failed to create database: {err}")
            logging.error(f"Failed to create database: {err}")
            sys.exit(1)

def connect_to_database():
    """
    Establishes a connection to the MySQL database using dynamic credentials.

    Returns:
        mysql.connector.connection.MySQLConnection: Database connection object.

    Raises:
        mysql.connector.Error: If connection fails due to incorrect credentials or database setup.
    """
    global MYSQL_PASSWORD
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        logging.info(f"Connected to database: {MYSQL_DATABASE}")
        return conn
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("[+] Default or stored MySQL password failed. Please enter the MySQL root password:")
            MYSQL_PASSWORD = getpass.getpass("[+] MySQL root password: ")
            try:
                conn = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DATABASE
                )
                logging.info(f"Connected to database: {MYSQL_DATABASE}")
                return conn
            except mysql.connector.Error as err:
                print(f"[+] Error: Failed to connect to database: {err}")
                print("[+] Ensure MySQL is running and the database 'student_db' exists.")
                print("[+] Run 'setup_database.sql' with your MySQL credentials to create the database and tables.")
                print(f"[+] Example: mysql -u {MYSQL_USER} -p < setup_database.sql")
                logging.error(f"Failed to connect to database: {err}")
                sys.exit(1)
        else:
            print(f"[+] Error: Failed to connect to database: {err}")
            print("[+] Ensure MySQL is running and the database 'student_db' exists.")
            print("[+] Run 'setup_database.sql' with your MySQL credentials to create the database and tables.")
            print(f"[+] Example: mysql -u {MYSQL_USER} -p < setup_database.sql")
            logging.error(f"Failed to connect to database: {err}")
            sys.exit(1)

def admin_login():
    """
    Authenticates an admin user by checking username and password against the database.
    Allows up to 3 login attempts before exiting.

    Returns:
        bool: True if login is successful, False otherwise.
    """
    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        print("\n[+] Admin Login")
        print("------------------------------------------------------")
        username = input("[+] Username: ").strip()
        password = getpass.getpass("[+] Password: ")
        attempts += 1

        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE username = %s AND password_hash = %s", (username, password))
            result = cursor.fetchone()
            conn.close()

            if result:
                print("[+] Login successful.")
                logging.info(f"Admin {username} logged in successfully")
                return True
            else:
                remaining = max_attempts - attempts
                print(f"[+] Invalid username or password. {remaining} attempts remaining.")
                logging.warning(f"Failed login attempt for username: {username}")
                if remaining == 0:
                    print("[+] Maximum login attempts exceeded.")
                    logging.error(f"Admin login failed: maximum attempts exceeded for {username}")
                    return False
        except mysql.connector.Error as err:
            print(f"[+] Error: Database error during login: {err}")
            logging.error(f"Database error during login for {username}: {err}")
            return False

def validate_student_data(name, age, gender, email, phone):
    """
    Validates student input data to ensure it meets required criteria.

    Args:
        name (str): Student's full name.
        age (str): Student's age.
        gender (str): Student's gender.
        email (str): Student's email.
        phone (str): Student's phone number.

    Returns:
        tuple: (bool, str) - (True if valid, error message if invalid).
    """
    if not name or len(name) < 2:
        return False, "Name must be at least 2 characters."
    try:
        age = int(age)
        if not 10 <= age <= 100:
            return False, "Age must be between 10 and 100."
    except ValueError:
        return False, "Age must be a valid number."
    if gender.upper() not in ['M', 'F', 'OTHER']:
        return False, "Gender must be M, F, or Other."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format."
    if not re.match(r"^\+?\d{10,15}$", phone):
        return False, "Phone number must be 10-15 digits."
    return True, ""

def register_student():
    """
    Registers a new student in the database with validated input.
    Generates a unique student ID based on the current count of students.
    """
    print("\n[+] Register New Student")
    print("------------------------------------------------------")
    name = input("[+] Full Name: ").strip()
    age = input("[+] Age: ").strip()
    gender = input("[+] Gender (M/F/Other): ").strip().upper()
    department = input("[+] Department: ").strip()
    email = input("[+] Email: ").strip()
    phone = input("[+] Phone Number: ").strip()

    # Validate input data
    is_valid, error = validate_student_data(name, age, gender, email, phone)
    if not is_valid:
        print(f"[+] Error: {error}")
        logging.error(f"Failed student registration: {error}")
        return

    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        # Generate unique student ID (e.g., S1001)
        cursor.execute("SELECT COUNT(*) FROM students")
        count = cursor.fetchone()[0] + 1
        student_id = f"S{1000 + count}"

        # Insert student data
        cursor.execute(
            """
            INSERT INTO students (student_id, name, age, gender, department, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (student_id, name, age, gender, department, email, phone)
        )
        conn.commit()
        print(f"[+] Student registered successfully. Assigned ID: {student_id}")
        logging.info(f"Student registered: {student_id} - {name}")
    except mysql.connector.Error as err:
        print(f"[+] Error: Failed to register student: {err}")
        logging.error(f"Error registering student {student_id}: {err}")
    finally:
        conn.close()

def edit_student():
    """
    Allows an admin to edit an existing student's details by searching for their name.
    Displays matching students, allows selection, and requires confirmation.
    """
    print("\n[+] Edit Student")
    print("------------------------------------------------------")
    name = input("[+] Enter student name (partial or full): ").strip()

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id, name, age, gender, department, email, phone FROM students WHERE name LIKE %s AND status = TRUE",
            (f"%{name}%",)
        )
        results = cursor.fetchall()

        if not results:
            print(f"[+] Error: No active students found matching '{name}'.")
            logging.warning(f"No active students found for edit with name: {name}")
            conn.close()
            return

        print(f"[+] Found {len(results)} matching student(s):")
        for idx, row in enumerate(results, 1):
            print(f"  {idx}. ID: {row[0]} | Name: {row[1]} | Age: {row[2]} | Gender: {row[3]} | Department: {row[4]} | Email: {row[5]} | Phone: {row[6]}")

        if len(results) > 1:
            try:
                choice = int(input("[+] Select student by number (1-%d): " % len(results)))
                if not 1 <= choice <= len(results):
                    print("[+] Error: Invalid selection.")
                    logging.warning(f"Invalid student selection for edit: {choice}")
                    conn.close()
                    return
            except ValueError:
                print("[+] Error: Please enter a valid number.")
                logging.warning(f"Invalid input for student selection in edit")
                conn.close()
                return
        else:
            choice = 1

        selected_student = results[choice - 1]
        student_id = selected_student[0]
        print(f"[+] Selected student: {selected_student[1]} (ID: {student_id})")
        confirm = input("[+] Confirm edit (y/n): ").strip().lower()
        if confirm != 'y':
            print("[+] Edit cancelled.")
            logging.info(f"Edit cancelled for student ID: {student_id}")
            conn.close()
            return

        print("[+] Enter new values (press Enter to keep current value):")
        name = input("[+] New Name: ").strip() or selected_student[1]
        age = input("[+] New Age: ").strip() or str(selected_student[2])
        gender = input("[+] New Gender (M/F/Other): ").strip().upper() or selected_student[3]
        department = input("[+] New Department: ").strip() or selected_student[4]
        email = input("[+] New Email: ").strip() or selected_student[5]
        phone = input("[+] New Phone Number: ").strip() or selected_student[6]

        # Validate input data
        is_valid, error = validate_student_data(name, age, gender, email, phone)
        if not is_valid:
            print(f"[+] Error: {error}")
            logging.error(f"Failed student edit for {student_id}: {error}")
            conn.close()
            return

        # Update student data
        cursor.execute(
            """
            UPDATE students
            SET name = %s, age = %s, gender = %s, department = %s, email = %s, phone = %s
            WHERE student_id = %s
            """,
            (name, int(age), gender, department, email, phone, student_id)
        )
        conn.commit()
        print(f"[+] Student {student_id} updated successfully.")
        logging.info(f"Student {student_id} updated by admin")
    except mysql.connector.Error as err:
        print(f"[+] Error: Failed to edit student: {err}")
        logging.error(f"Error editing student with name '{name}': {err}")
    finally:
        conn.close()

def delete_student():
    """
    Allows an admin to mark a student as inactive (soft delete) by searching for their name.
    Displays matching students, allows selection, and requires confirmation.
    """
    print("\n[+] Delete Student")
    print("------------------------------------------------------")
    name = input("[+] Enter student name (partial or full): ").strip()

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id, name, age, gender, department, email, phone FROM students WHERE name LIKE %s AND status = TRUE",
            (f"%{name}%",)
        )
        results = cursor.fetchall()

        if not results:
            print(f"[+] Error: No active students found matching '{name}'.")
            logging.warning(f"No active students found for delete with name: {name}")
            conn.close()
            return

        print(f"[+] Found {len(results)} matching student(s):")
        for idx, row in enumerate(results, 1):
            print(f"  {idx}. ID: {row[0]} | Name: {row[1]} | Age: {row[2]} | Gender: {row[3]} | Department: {row[4]} | Email: {row[5]} | Phone: {row[6]}")

        if len(results) > 1:
            try:
                choice = int(input("[+] Select student by number (1-%d): " % len(results)))
                if not 1 <= choice <= len(results):
                    print("[+] Error: Invalid selection.")
                    logging.warning(f"Invalid student selection for delete: {choice}")
                    conn.close()
                    return
            except ValueError:
                print("[+] Error: Please enter a valid number.")
                logging.warning(f"Invalid input for student selection in delete")
                conn.close()
                return
        else:
            choice = 1

        selected_student = results[choice - 1]
        student_id = selected_student[0]
        print(f"[+] Selected student: {selected_student[1]} (ID: {student_id})")
        confirm = input("[+] Confirm deletion (y/n): ").strip().lower()
        if confirm != 'y':
            print("[+] Deletion cancelled.")
            logging.info(f"Deletion cancelled for student ID: {student_id}")
            conn.close()
            return

        # Mark student as inactive
        cursor.execute(
            "UPDATE students SET status = FALSE WHERE student_id = %s",
            (student_id,)
        )
        conn.commit()
        print(f"[+] Student {student_id} marked as inactive successfully.")
        logging.info(f"Student {student_id} marked as inactive by admin")
    except mysql.connector.Error as err:
        print(f"[+] Error: Failed to delete student: {err}")
        logging.error(f"Error deleting student with name '{name}': {err}")
    finally:
        conn.close()

def view_students():
    """
    Displays all active students from the database.
    """
    print("\n[+] All Registered Students")
    print("------------------------------------------------------")
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id, name, department, email, phone FROM students WHERE status = TRUE"
        )
        results = cursor.fetchall()

        if results:
            for row in results:
                print(f"[+] ID: {row[0]} | Name: {row[1]} | Department: {row[2]} | Email: {row[3]} | Phone: {row[4]}")
        else:
            print("[+] No students found.")
        conn.close()
    except mysql.connector.Error as err:
        print(f"[+] Error: Failed to retrieve students: {err}")
        logging.error(f"Error retrieving students: {err}")

def search_students():
    """
    Searches for students by name or department (case-insensitive).
    """
    print("\n[+] Search Students")
    print("------------------------------------------------------")
    keyword = input("[+] Enter name or department: ").strip()

    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT student_id, name, department, email, phone
            FROM students
            WHERE (name LIKE %s OR department LIKE %s) AND status = TRUE
            """,
            (f"%{keyword}%", f"%{keyword}%")
        )
        results = cursor.fetchall()

        if results:
            for row in results:
                print(f"[+] ID: {row[0]} | Name: {row[1]} | Department: {row[2]} | Email: {row[3]} | Phone: {row[4]}")
        else:
            print("[+] No matching students found.")
        conn.close()
    except mysql.connector.Error as err:
        print(f"[+] Error: Failed to search students: {err}")
        logging.error(f"Error searching students with keyword '{keyword}': {err}")

def export_to_csv():
    """
    Exports all active students to a CSV file with a timestamped filename.
    """
    print("\n[+] Export Students to CSV")
    print("------------------------------------------------------")
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id, name, age, gender, department, email, phone FROM students WHERE status = TRUE"
        )
        results = cursor.fetchall()

        if not results:
            print("[+] No students to export.")
            logging.info("No students found for CSV export")
            conn.close()
            return

        # Create timestamped filename
        filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Student ID", "Name", "Age", "Gender", "Department", "Email", "Phone"])
            writer.writerows(results)
        print(f"[+] Data exported to {filename}")
        logging.info(f"Data exported to {filename}")
        conn.close()
    except mysql.connector.Error as err:
        print(f"[+] Error: Failed to export students: {err}")
        logging.error(f"Error exporting students to CSV: {err}")
    except IOError as err:
        print(f"[+] Error: Failed to write to CSV file: {err}")
        logging.error(f"Error writing to CSV file {filename}: {err}")

def show_admin_menu():
    """
    Displays the command-line interface menu for admin users with a professional layout.
    """
    print("\n[+] EduEnroll CLI - Admin Menu")
    print("------------------------------------------------------")
    print("1. Edit Student")
    print("2. Delete Student")
    print("3. View All Students")
    print("4. Search Students")
    print("5. Export Student Data to CSV")
    print("6. Return to Main Menu")
    print("7. Exit Program")
    print("------------------------------------------------------")

def show_student_menu():
    """
    Displays the command-line interface menu for student users with a professional layout.
    """
    print("\n[+] EduEnroll CLI - Student Menu")
    print("------------------------------------------------------")
    print("1. Register as Student")
    print("2. View All Students")
    print("3. Search Students")
    print("4. Return to Main Menu")
    print("5. Exit Program")
    print("------------------------------------------------------")

def main():
    """
    Main function to run the EduEnroll CLI application.
    Sets up environment, displays role selection, and directs to appropriate menu.
    """
    # Setup environment before running the application
    setup_environment()

    while True:
        print("\n[+] EduEnroll CLI")
        print("------------------------------------------------------")
        print("EduEnroll is a command-line interface for student registration and management created by Group 11")
        print("------------------------------------------------------")
        print("""
This project is more than code—it's a testament to our growth, a reflection of our dreams, and a step toward changing the world, one solution at a time.
------------------------------------------------------
""")
        print("Please select your role to continue:")
        print("1. Admin")
        print("2. Student")
        print("3. Exit")
        print("------------------------------------------------------")
        role_choice = input("[+] Enter choice (1, 2, or 3): ").strip()

        if role_choice == "1":
            # Admin role requires authentication
            if not admin_login():
                print("[+] Exiting program due to failed login.")
                logging.error("Program exited due to failed admin login")
                sys.exit(1)

            # Admin menu loop
            while True:
                show_admin_menu()
                choice = input("[+] Enter choice (1-7): ").strip()

                if choice == "1":
                    edit_student()
                elif choice == "2":
                    delete_student()
                elif choice == "3":
                    view_students()
                elif choice == "4":
                    search_students()
                elif choice == "5":
                    export_to_csv()
                elif choice == "6":
                    print("[+] Returning to main menu.")
                    logging.info("Admin returned to main menu")
                    break
                elif choice == "7":
                    print("[+] Exiting EduEnroll. Goodbye!")
                    logging.info("Program exited normally from admin menu")
                    sys.exit(0)
                else:
                    print("[+] Invalid choice. Please select a valid option (1-7).")
                    logging.warning(f"Invalid admin menu choice: {choice}")

        elif role_choice == "2":
            # Student menu loop (no login required)
            while True:
                show_student_menu()
                choice = input("[+] Enter choice (1-5): ").strip()

                if choice == "1":
                    register_student()
                elif choice == "2":
                    view_students()
                elif choice == "3":
                    search_students()
                elif choice == "4":
                    print("[+] Returning to main menu.")
                    logging.info("Student returned to main menu")
                    break
                elif choice == "5":
                    print("[+] Exiting EduEnroll. Goodbye!")
                    logging.info("Program exited normally from student menu")
                    sys.exit(0)
                else:
                    print("[+] Invalid choice. Please select a valid option (1-5).")
                    logging.warning(f"Invalid student menu choice: {choice}")

        elif role_choice == "3":
            print("[+] Exiting EduEnroll. Goodbye!")
            logging.info("Program exited normally via role selection")
            sys.exit(0)

        else:
            print("[+] Invalid role selection. Please choose 1 (Admin), 2 (Student), or 3 (Exit).")
            logging.warning(f"Invalid role choice: {role_choice}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[+] Program terminated by user.")
        logging.info("Program terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"[+] Unexpected error: {e}")
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)