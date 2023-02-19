from abc import ABC, abstractmethod
import mpmath
from database import create_connection, get_current_index, raise_current_index

# Contains all the Classes for Irrational numbers

# For rounding reasons, mpmath.mp.dps must be set 1 higher and the resulting string
# must be cut by the last digit in most functions.


class IrrationalDigits(ABC):

    @staticmethod
    @abstractmethod
    def get_digit_at_index(index):
        pass

    @staticmethod
    @abstractmethod
    def get_last_ten_digits(txt_path):
        pass

    @staticmethod
    @abstractmethod
    def get_next_ten_digits_for_user(user, db_path):
        pass

    @staticmethod
    @abstractmethod
    def get_next_ten_digits_from_index(index):
        pass

    @staticmethod
    @abstractmethod
    def get_all_from_file(txt_path):
        pass

    @staticmethod
    @abstractmethod
    def get_digits_up_to(index):
        pass


class Pi(IrrationalDigits):
    @staticmethod
    def get_digit_at_index(index):
        try:  # index might be invalid
            if int(index) < 0:
                return "error: index too small"
            if int(index) == 0:  # Special case for first digit before "."
                return "3"
            mpmath.mp.dps = int(index) + 2
            return str(mpmath.pi)[-2]
        except ValueError:
            return "error: invalid index"

    @staticmethod
    def get_last_ten_digits(txt_path):
        with open(txt_path, "a+") as f:
            f.seek(0)
            number_of_digits = len(f.readline())
            if number_of_digits == 0:  # the first ten digits contain a "." that needs to be adjusted for
                number_of_digits = 1
            mpmath.mp.dps = number_of_digits + 10
            pi = str(mpmath.pi)
            f.seek(0)
            f.truncate()
            f.write(pi)
            if number_of_digits == 1:
                return pi[-12:-1]
            return pi[-12:-2]

    @staticmethod
    def get_next_ten_digits_for_user(user, db_path):
        conn = create_connection(db_path)
        current_index = get_current_index(conn, user)
        if current_index < 0:
            return "error: user not found"
        pi_string = Pi.get_next_ten_digits_from_index(current_index)
        raise_current_index(conn, user, 10)
        return pi_string

    @staticmethod
    def get_next_ten_digits_from_index(index):
        mpmath.mp.dps = int(index) + 11
        if int(index) == 0:  # Special case for first digit before "."
            return str(mpmath.pi)[-12:-1]
        else:
            return str(mpmath.pi)[-11:-1]

    @staticmethod
    def get_all_from_file(txt_path):
        with open(txt_path, "a+") as f:
            f.seek(0)
            line = f.readline()
            if len(line) == 0:
                return "empty"
            return line[:-1]

    @staticmethod
    def get_digits_up_to(index):
        if index <= 0:
            return "3"
        mpmath.mp.dps = index + 2
        return str(mpmath.pi)[:-1]


class E(IrrationalDigits):
    @staticmethod
    def get_digit_at_index(index):
        try:  # index might be invalid
            if int(index) < 0:
                return "error: index too small"
            if int(index) == 0:  # Special case for first digit before "."
                return "2"
            mpmath.mp.dps = int(index) + 2
            return str(mpmath.e)[-2]
        except ValueError:
            return "error: invalid index"

    @staticmethod
    def get_last_ten_digits(txt_path):
        with open(txt_path, "a+") as f:
            f.seek(0)
            number_of_digits = len(f.readline())
            if number_of_digits == 0:  # the first ten digits contain a "." that needs to be adjusted for
                number_of_digits = 1
            mpmath.mp.dps = number_of_digits + 10
            e = str(mpmath.e)
            f.seek(0)
            f.truncate()
            f.write(e)
            if number_of_digits == 1:
                return e[-12:-1]
            return e[-12:-2]

    @staticmethod
    def get_next_ten_digits_for_user(user, db_path):
        conn = create_connection(db_path)
        current_index = get_current_index(conn, user)
        if current_index < 0:
            return "error: user not found"
        e_string = E.get_next_ten_digits_from_index(current_index)
        raise_current_index(conn, user, 10)
        return e_string

    @staticmethod
    def get_next_ten_digits_from_index(index):
        mpmath.mp.dps = int(index) + 11
        if int(index) == 0:  # Special case for first digit before "."
            return str(mpmath.e)[-12:-1]
        else:
            return str(mpmath.e)[-11:-1]

    @staticmethod
    def get_all_from_file(txt_path):
        with open(txt_path, "a+") as f:
            f.seek(0)
            line = f.readline()
            if len(line) == 0:
                return "empty"
            return line[:-1]

    @staticmethod
    def get_digits_up_to(index):
        if index <= 0:
            return "2"
        mpmath.mp.dps = index + 2
        return str(mpmath.e)[:-1]
