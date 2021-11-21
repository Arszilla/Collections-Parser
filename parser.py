import os
import shutil
import sqlite3

from validate_email import validate_email


class LineParser:
    @staticmethod
    def parse_line_seperator(line, seperator, seperator_name):
        line_type = ""
        email = ""
        username = ""
        password = ""

        if line.count(seperator) == 1:
            split_line = line.split(seperator)

            if validate_email(split_line[0]):
                line_type = "user_or_mail_%s_pass" % seperator_name
                username = split_line[0]
                email = split_line[0]

            else:
                line_type = "user_or_mail_%s_pass" % seperator_name
                username = split_line[0]

            password = split_line[1]

            return True, username, email, password, line_type

        return False, "", "", "", ""

    @staticmethod
    def parse_lines(line):
        line_type = ""
        email = ""
        username = ""
        password = ""

        # Case: mail@mail.com:password
        # Case: username:password
        # Case: mail@mail.com;password
        # Case: username;password

        good, username, email, password, line_type = LineParser.parse_line_seperator(line,
                                                                                     ':',
                                                                                     "doubledots_or_dotcomma")

        if not good:
            good, username, email, password, line_type = LineParser.parse_line_seperator(line,
                                                                                         ';',
                                                                                         "doubledots_or_dotcomma")

        if good:
            return {"type": line_type,
                    "mail": email,
                    "user": username,
                    "pass": password}


class LeakParser:
    def __init__(self, leak_path):
        self.max_line_length = 200
        self.min_line_length = 3
        self.linebreaks = ["\r\n",
                           "\r",
                           "\n"]

        self.collections_dict = {}
        self.subcollections_dict = {}

        self.collection = ""
        self.subcollection = ""
        self.collection_id = 0
        self.subcollection_id = 0

        self.leak_path = leak_path

        self.connection = None
        self.cursor = None
        self.initiate_database()

        self.get_collections()
        self.set_collection()

        self.open_leak = open(self.leak_path, "rb")
        self.leak_cache = ""

        self.current_cache = 0
        self.current_line_start = 0
        self.current_line_end = 0

        self.eof = False

        self.line_error = False

        self.parse_to_database_counter = 0

        self.parse_to_database = self.parse_to_database_actual

    def initiate_database(self):
        try:
            # Attempt to create or connect to the database:
            self.connection = sqlite3.connect("credentials.sqlite")
            self.connection.text_factory = str

            # Create tables, if they don't exist already:
            self.create_collections_table = """CREATE TABLE IF NOT EXISTS collections (
                collection_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                collection_name TEXT
                )"""

            self.create_subcollections_table = """CREATE TABLE IF NOT EXISTS subcollections (
                subcollection_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                subcollection_name TEXT
                )"""

            self.create_credentials_table = """CREATE TABLE IF NOT EXISTS credentials (
                collection INTEGER, 
                subcollection INTEGER, 
                username TEXT, 
                email TEXT, 
                password TEXT
                )"""

            self.connection.execute(self.create_collections_table)
            self.connection.execute(self.create_subcollections_table)
            self.connection.execute(self.create_credentials_table)

            # Create a cursor object:
            self.cursor = self.connection.cursor()

        except sqlite3.Error as error:
            pass

    def update_cache(self):
        if self.eof:
            return

        if len(self.leak_cache)-self.current_cache > self.max_line_length:
            return

        new_read = self.open_leak.read(0x1000000)

        if len(new_read) < 0x1000000:
            self.eof = True

        self.leak_cache = self.leak_cache[self.current_cache:] + new_read
        self.current_cache = 0

    def update_current_line(self):
        self.update_cache()

        for linebreak in self.linebreaks:
            try:
                leak_index = self.leak_cache.index(linebreak,
                                                   self.current_cache,
                                                   self.current_cache + self.max_line_length)

                self.current_line_start = self.current_cache
                self.current_line_end = leak_index + len(linebreak)
                self.current_cache = self.current_line_end

                return

            except:
                continue

        if self.eof and (len(self.leak_cache) - self.current_cache <= self.max_line_length) and (len(self.leak_cache) - self.current_cache != 0):
            self.current_line_start = self.current_cache
            self.current_cache = len(self.leak_cache)
            self.current_line_end = self.current_cache

            return

        self.line_error = True

    def get_current_line(self):
        return self.leak_cache[self.current_line_start:self.current_line_end].strip()

    def set_collection(self):
        script_path = os.path.dirname(os.path.realpath(__file__))

        relative_leak_path = os.path.relpath(self.leak_path, script_path)

        directory = os.path.normpath(relative_leak_path)
        directory = directory.split(os.sep)

        self.collection = str(directory[0])
        self.subcollection = str(directory[1])

        if not self.collections_dict.has_key(self.collection):
            self.add_collection(self.collection)

        if not self.subcollections_dict.has_key(self.subcollection):
            self.add_subcollection(self.subcollection)

        self.collection_id = self.collections_dict[self.collection]
        self.subcollection_id = self.subcollections_dict[self.subcollection]

    def add_collection(self, collection):
        # print "Collection:", collection

        sql_query = """INSERT INTO collections (collection_name) VALUES (?)"""

        self.cursor.execute(sql_query,
                            (collection,))
        self.get_collections()

    def add_subcollection(self, subcollection):
        # print "Subcollection:", subcollection

        sql_query = """INSERT INTO subcollections (subcollection_name) VALUES (?)"""

        self.cursor.execute(sql_query,
                            (subcollection,))
        self.get_collections()

    def get_collections(self):
        self.collections_dict = {}
        
        sql_query = self.cursor.execute("SELECT * FROM collections")

        for row in sql_query:
            self.collections_dict[str(row[1])] = row[0]

        self.subcollections_dict = {}

        sql_query = self.cursor.execute("SELECT * FROM subcollections")

        for row in sql_query:
            self.subcollections_dict[str(row[1])] = row[0]

        # print self.collections_dict
        # print self.subcollections_dict

    def parse_to_database_test(self, info):
        if self.parse_to_database_counter % 20000 == 0:
            if info:
                print "File format type:", repr(info)

        self.parse_to_database_counter += 1

    def parse_to_database_actual(self, info):
        if self.parse_to_database_counter % 20000 == 0:
            if info:
                print "File format type:", repr(info)

        self.parse_to_database_counter += 1

        if info:
            sql_query = """INSERT INTO credentials (collection, subcollection, username, email, password) VALUES (?, ?, ?, ?, ?)"""

            self.cursor.execute(sql_query,
                                (self.collection_id,
                                 self.subcollection_id,
                                 str(info["user"]),
                                 str(info["mail"]),
                                 str(info["pass"]),))

    def run(self):
        inconsistency_list = []

        inconsistency_status = False

        self.update_current_line()

        line_1 = LineParser.parse_lines(self.get_current_line())
        line_2 = LineParser.parse_lines(self.get_current_line())
        line_3 = LineParser.parse_lines(self.get_current_line())
        line_4 = LineParser.parse_lines(self.get_current_line())
        line_5 = LineParser.parse_lines(self.get_current_line())

        if self.line_error or not(line_1 != None and
                                  line_2 != None and
                                  line_3 != None and
                                  line_4 != None and
                                  line_5 != None and
                                  line_1["type"] == line_2["type"] and
                                  line_2["type"] == line_3["type"] and
                                  line_3["type"] == line_4["type"] and
                                  line_4["type"] == line_5["type"]):

            print "File is inconsistent by the first few lines!"

            inconsistency_status = True

        if not inconsistency_status:
            FileLeakType = line_1["type"]

            print "FileLeakType:", FileLeakType

            inconsistency_counter = 0

            self.parse_to_database(line_1)
            self.parse_to_database(line_2)
            self.parse_to_database(line_3)
            self.parse_to_database(line_4)
            self.parse_to_database(line_5)

            while not self.line_error:
                self.update_current_line()

                line = LineParser.parse_lines(self.get_current_line())

                if not line or line["type"] != FileLeakType:
                    inconsistency_counter += 1
                    inconsistency_list.append(self.get_current_line())

                    if len(inconsistency_list) > 10:
                        inconsistency_list = inconsistency_list[-10:]

                else:
                    if inconsistency_counter:
                        inconsistency_counter -= 1

                if inconsistency_counter >= 10:
                    print "Careful! Too many inconsistencies! Breaking!"

                    inconsistency_status = True

                    break

                self.parse_to_database(line)

        if inconsistency_status:
            with open("inconsistencies.txt", "a+b") as inconsistency_log:
                inconsistency_log.write(self.leak_path + ": " + repr(inconsistency_list) + "\r\n")
                inconsistency_log.close()

        else:
            with open("consistences.txt", "a+b") as consistency_log:
                consistency_log.write(self.leak_path + "\r\n")
                consistency_log.close()

        self.connection.commit()


def manage_files(file):
    try:
        print "Managing file:", file

        leakparser_class = LeakParser(file)

        print "Parsing Collection:", leakparser_class.collection
        print "Parsing subcollection:", leakparser_class.subcollection

        leakparser_class.run()
        leakparser_class.open_leak.close()

        shutil.move(file, file + ".PARSED")

    except Exception as error:
        with open("exceptions.txt", "a+b") as exception_log:
            exception_log.write(file + ": " + repr(error.message) + " - " + repr(error.args) + "\r\n")
            exception_log.close()


def recurse_files(pwd):
    for folder in os.listdir(pwd):
        if "NOTPARSED" not in folder and "PARSED" not in folder:
            if os.path.isdir(pwd + "/" + folder):
                recurse_files(pwd + "/" + folder)

            else:
                manage_files(pwd + "/" + folder)


if __name__ == "__main__":
    recurse_files(os.path.dirname(os.path.realpath(__file__)))
